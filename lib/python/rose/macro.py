# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-3 Met Office.
# 
# This file is part of Rose, a framework for scientific suites.
# 
# Rose is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Rose is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Rose. If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------------------------------------------
"""
Module to list or run available custom macros for a configuration.

It also stores macro base classes and macro library functions.

"""

import copy
import inspect
import os
import re
import sys

import rose.config
import rose.formats.namelist
from rose.opt_parse import RoseOptionParser
import rose.resource
import rose.variable


ALLOWED_MACRO_CLASS_METHODS = ["transform", "validate",
                               "downgrade", "upgrade"]
ERROR_LOAD_CONFIG_DIR = "{0}: not an application directory.\n"
ERROR_LOAD_MACRO = "Could not load macro {0}: {1}"
ERROR_LOAD_METADATA = "Could not load metadata {0}\n"
ERROR_LOAD_CHOSEN_META_PATH = "Could not find metadata for {0}, using {1}\n"
ERROR_LOAD_META_PATH = "Could not find metadata for {0}\n"
ERROR_LOAD_CONF_META_NODE = "Error: could not find meta flag"
ERROR_MACRO_NOT_FOUND = "Error: could not find macro {0}\n"
ERROR_NO_MACROS = "Please specify a macro name.\n"
MACRO_DIRNAME = os.path.join(os.path.join("lib", "python"), "macros")
MACRO_EXT = ".py"
MACRO_OUTPUT_HELP = "    # {0}"
MACRO_OUTPUT_ID = "[{0}] {2}"
MACRO_OUTPUT_TRANSFORM_CHANGES = "{0}: changes: {1}\n"
MACRO_OUTPUT_VALIDATE_ISSUES = "{0}: issues: {1}\n"
MACRO_OUTPUT_WARNING_ISSUES = "{0}: warnings: {1}\n"
REC_MODIFIER = re.compile(r"\{.+\}")
REC_ID_STRIP_DUPL = re.compile(r"\([\d:, ]+\)")
REC_ID_STRIP = re.compile('(?:\{.+\})?(?:\([\d:, ]+\))?$')
PROBLEM_ENTRY = "    {0}={1}={2}\n        {3}\n"
PROMPT_ACCEPT_CHANGES = "Accept y/n (default n)? "
PROMPT_OK = "y"
SETTING_ID = "    {0}={1}={2}\n        {3}"
TRANSFORM_METHOD = "transform"
VALIDATE_METHOD = "validate"
VERBOSE_LIST = "{0} - ({1}) - {2}"


class MacroValidateError(Exception):

    """Raise this error if validation parsing fails."""

    def __init__(self, *args):
        args = list(args)
        for i, arg in enumerate(args):
            if issubclass(type(arg), Exception):
                args[i] = str(type(arg)) + " " + str(arg)
        self.args_string = " ".join([str(a) for a in args])
        super(MacroValidateError, self).__init__()

    def __str__(self):
        return 'Could not perform validation: ' + self.args_string


class MacroBase(object):

    """Base class for macros for validating or transforming configurations."""

    def __init__(self):
        self.reports = []  # MacroReport instances for errors or changes

    def _get_section_option_from_id(self, var_id):
        """Return a configuration section and option from an id."""
        section_option = var_id.split(rose.CONFIG_DELIMITER, 1)
        if len(section_option) == 1:
            return var_id, None
        return section_option

    def _get_id_from_section_option(self, section, option):
        """Return a variable id from a section and option."""
        if option is None:
            return section
        return section + rose.CONFIG_DELIMITER + option

    def _sorter(self, rep1, rep2):
        # Sort [section], [section, option], [section, None]
        id1 = self._get_id_from_section_option(rep1.section, rep1.option)
        id2 = self._get_id_from_section_option(rep2.section, rep2.option)
        if id1 == id2:
            return cmp(rep1.value, rep2.value)
        return rose.config.sort_settings(id1, id2)

    def _load_meta_config(self, config, meta=None, directory=None):
        """Return a metadata configuration object."""
        if isinstance(meta, rose.config.ConfigNode):
            return meta
        return load_meta_config(config, directory)

    def get_metadata_for_config_id(self, setting_id, meta_config):
        return get_metadata_for_config_id(setting_id, meta_config)

    def get_resource_path(self, filename=''):
        """Load the resource according to the path of the calling macro.
        
        The returned path will be based on the macro location under
        lib/python in the metadata directory.

        If the calling macro is lib/python/macro/levels.py,
        and the filename is 'rules.json', the returned path will be
        etc/macro/levels/rules.json .
        
        """
        last_frame = inspect.getouterframes(inspect.currentframe())[1]
        macro_path = os.path.abspath(inspect.getfile(last_frame[0]))
        macro_name = os.path.basename(macro_path).rpartition('.py')[0]
        macro_root_dir = os.path.dirname(macro_path)
        library_dir = os.path.dirname(os.path.dirname(macro_root_dir))
        root_dir = os.path.dirname(library_dir)
        # root_dir is the directory of the rose-meta.conf file.
        etc_path = os.path.join(root_dir, 'etc')
        resource_path = os.path.join(etc_path, 'macros')
        resource_path = os.path.join(resource_path, macro_name)
        resource_path = os.path.join(resource_path, filename)
        return resource_path

    def pretty_format_config(self, config):
        """Pretty-format the configuration values."""
        pretty_format_config(config)

    def standard_format_config(self, config):
        """Standardise configuration syntax."""
        standard_format_config(config)

    def add_report(self, *args, **kwargs):
        self.reports.append(MacroReport(*args, **kwargs))


class MacroValidatorCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroValidatorCollection, self).__init__()

    def validate(self, config, meta_config):
        for macro_inst in self.macros:
            if not hasattr(macro_inst, VALIDATE_METHOD):
                continue
            macro_method = getattr(macro_inst, VALIDATE_METHOD)
            p_list = macro_method(config, meta_config)
            p_list.sort(self._sorter)
            self.reports += p_list
        return self.reports 


class MacroTransformerCollection(MacroBase):

    """Collate several macros into one."""

    def __init__(self, *macros):
        self.macros = macros
        super(MacroTransformerCollection, self).__init__()

    def transform(self, config, meta_config=None):
        for macro_inst in self.macros:
            if not hasattr(macro_inst, TRANSFORM_METHOD):
                continue
            macro_method = getattr(macro_inst, TRANSFORM_METHOD)
            config, c_list = macro_method(config, meta_config)
            c_list.sort(self._sorter)
            self.reports += c_list
        return config, self.reports


class MacroReport(object):

    """Class to hold information about a macro issue."""

    def __init__(self, section=None, option=None, value=None,
                 info=None, is_warning=False):
        self.section = section
        self.option = option
        self.value = value
        self.info = info
        self.is_warning = is_warning


def add_site_meta_paths():
    """Load any metadata paths specified in a user or site configuration."""
    conf = rose.resource.ResourceLocator.default().get_conf()
    path = conf.get_value([rose.CONFIG_SECT_TOP, rose.CONFIG_OPT_META_PATH])
    if path is not None:
        for path in path.split(os.pathsep):
            path = os.path.expanduser(os.path.expandvars(path))
            sys.path.insert(0, os.path.abspath(path))
    sys.path.append(os.path.join(os.getenv("ROSE_HOME"), "etc/rose-meta"))


def add_env_meta_paths():
    """Load the environment variable ROSE_META_PATH, if defined."""
    path = os.environ.get("ROSE_META_PATH")
    if path is not None:
        for path in path.split(os.pathsep):
            path = os.path.expanduser(os.path.expandvars(path))
            sys.path.insert(0, os.path.abspath(path))


def add_opt_meta_paths(meta_paths):
    """Load any metadata paths in a list of ":"-separated strings."""
    if meta_paths is not None:
        meta_paths.reverse()
        for child_paths in [arg.split(os.pathsep) for arg in meta_paths]:
            child_paths.reverse()
            for path in child_paths:
                path = os.path.expandvars(os.path.expanduser(path))
                sys.path.insert(0, os.path.abspath(path))


def load_meta_path(config=None, directory=None, is_upgrade=False,
                   locator=None):
    """Retrieve the path to the configuration metadata directory.

    Arguments:
        config - a rose config, perhaps with a meta= or project= flag
        directory - the directory of the rose config file
        is_upgrade - if True, load the path in an upgrade-specific way
        locator - a rose.resource.ResourceLocator instance.

    Returns the path to(or None) and a warning message (or None).

    """
    if config is None:
        config = rose.config.ConfigNode()
    warning = None
    if directory is not None and not is_upgrade:
        config_meta_dir = os.path.join(directory, rose.CONFIG_META_DIR)
        meta_file = os.path.join(config_meta_dir, rose.META_CONFIG_NAME)
        if os.path.isfile(meta_file):
            return config_meta_dir, warning
    if locator is None:
        locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = opt_node is None
    if opt_node is None:
        opt_node = config.get([rose.CONFIG_SECT_TOP,
                               rose.CONFIG_OPT_PROJECT], no_ignore=True)
    if opt_node is None or not opt_node.value:
        meta_keys = ["rose-all"]
    else:
        key = opt_node.value
        if "/" not in key:
            key = key + "/" + rose.META_DEFAULT_VN_DIR
        meta_keys = [key]
        if is_upgrade:
            meta_keys = [key.split("/")[0]]
        else:
            default_key = (key.rsplit("/", 1)[0] + "/" +
                           rose.META_DEFAULT_VN_DIR)
            if default_key != key:
                meta_keys.append(default_key)
    for i, meta_key in enumerate(meta_keys):
        path = os.path.join(meta_key, rose.META_CONFIG_NAME)
        if is_upgrade:
            path = meta_key
        try:
            meta_path = locator.locate(path)
        except rose.resource.ResourceError:
            continue
        else:
            if not ignore_meta_error and i > 0:
                warning = ERROR_LOAD_CHOSEN_META_PATH.format(meta_keys[0],
                                                             meta_keys[i])
            if is_upgrade:
                return meta_path, warning
            return os.path.dirname(meta_path), warning
    if not ignore_meta_error:
        warning = ERROR_LOAD_META_PATH.format(meta_keys[0])
    return None, warning


def load_meta_config(config, directory=None, error_handler=None):
    """Return the metadata config for a configuration."""
    if error_handler is None:
        error_handler = _report_error
    meta_config = rose.config.ConfigNode()
    meta_list = ['rose-all/' + rose.META_CONFIG_NAME]
    config_meta_path, warning = load_meta_path(config, directory)
    if warning is not None:
        error_handler(text=warning)
    if config_meta_path is not None:
        path = os.path.join(config_meta_path, rose.META_CONFIG_NAME)
        if path not in meta_list:
            meta_list.append(path)
    locator = rose.resource.ResourceLocator(paths=sys.path)
    opt_node = config.get([rose.CONFIG_SECT_TOP,
                           rose.CONFIG_OPT_META_TYPE], no_ignore=True)
    ignore_meta_error = opt_node is None
    config_loader = rose.config.ConfigLoader()
    for meta_key in meta_list:
        try:
            meta_path = locator.locate(meta_key)
        except rose.resource.ResourceError as e:
            if not ignore_meta_error:
                error_handler(text=ERROR_LOAD_META_PATH.format(meta_key))
        else:
            try:
                config_loader.load_with_opts(meta_path, meta_config)
            except rose.config.ConfigSyntaxError as e:
                error_handler(text=str(e))
    return meta_config


def load_meta_macro_modules(meta_files):
    """Import metadata macros and return them in an array."""
    modules = []
    for meta_file in meta_files:
        meta_dir = os.path.dirname(meta_file)
        if (not meta_dir.endswith(MACRO_DIRNAME) or
            not meta_file.endswith(MACRO_EXT)):
            continue
        macro_name = os.path.basename(meta_file).rpartition(MACRO_EXT)[0]
        sys.path.append(os.path.abspath(meta_dir))
        try:
            modules.append(__import__(macro_name))
        except Exception as e:
            info = ERROR_LOAD_MACRO.format(meta_file, e)
            sys.stderr.write(info + "\n")
        sys.path.pop()
    modules.sort()
    return modules


def get_macro_class_methods(macro_modules):
    """Return all macro methods in the modules."""
    macro_methods = []
    for macro_module in macro_modules:
        macro_name = macro_module.__name__
        contents = inspect.getmembers(macro_module)
        for obj_name, obj in contents:
            if not inspect.isclass(obj):
                continue
            for att_name in ALLOWED_MACRO_CLASS_METHODS:
                if (hasattr(obj, att_name) and
                    callable(getattr(obj, att_name))):
                    doc_string = obj.__doc__
                    macro_methods.append((macro_name, obj_name, att_name,
                                          doc_string))
    macro_methods.sort(lambda x, y: cmp(x[1], y[1]))
    macro_methods.sort(lambda x, y: cmp(x[0], y[0]))
    macro_methods.sort(lambda x, y: cmp(y[2], x[2]))
    return macro_methods


def get_macros_for_config(app_config=None,
                          config_directory=None,
                          return_modules=False,
                          include_system=False):
    """Driver function to return macro names for a config object."""
    if app_config is None:
        app_config = rose.config.ConfigNode()
    meta_path, warning = load_meta_path(app_config, config_directory)
    if meta_path is None:
        sys.exit(ERROR_LOAD_METADATA.format(""))
    meta_filepaths = []
    for dirpath, dirnames, filenames in os.walk(meta_path):
        if "/.svn" in dirpath:
            continue
        for fname in filenames:
            meta_filepaths.append(os.path.join(dirpath, fname))
    modules = load_meta_macro_modules(meta_filepaths)
    if include_system:
        import rose.macros  # Done to avoid cyclic top-level imports.
        modules.append(rose.macros)
    if return_modules:
        return get_macro_class_methods(modules), modules
    return get_macro_class_methods(modules)


def validate_config(app_config, meta_config, run_macro_list, modules,
                    macro_info_tuples):
    """Run validator custom macros on the config and return problems."""
    macro_problem_dict = {}
    for module_name, class_name, method, help in macro_info_tuples:
        macro_name = ".".join([module_name, class_name])
        if macro_name in run_macro_list and method == VALIDATE_METHOD:
            for module in modules:
                if module.__name__ == module_name:
                    macro_inst = getattr(module, class_name)()
                    macro_meth = getattr(macro_inst, method)
                    break
            problem_list = macro_meth(app_config, meta_config)
            if problem_list:
                macro_problem_dict.update({macro_name: problem_list})
    return macro_problem_dict


def transform_config(config, meta_config, transformer_macro, modules,
                     macro_info_tuples):
    """Run transformer custom macros on the config and return problems."""
    macro_change_dict = {}
    for module_name, class_name, method, help in macro_info_tuples:
        if method != TRANSFORM_METHOD:
            continue
        macro_name = ".".join([module_name, class_name])
        if macro_name != transformer_macro:
            continue
        for module in modules:
            if module.__name__ == module_name:
                macro_inst = getattr(module, class_name)()
                macro_method = getattr(macro_inst, method)
                break
        return macro_method(config, meta_config)
    return config, []


def pretty_format_config(config):
    """Improve configuration prettiness."""
    for keylist, node in config.walk():
        if len(keylist) == 2:
            scheme, option = keylist
            if ":" in scheme:
                scheme = scheme.split(":", 1)[0]
            try:
                scheme_module = getattr(rose.formats, scheme)
                pretty_format = getattr(scheme_module, "pretty_format")
            except AttributeError:
                continue
            values = rose.variable.array_split(node.value, ",")
            node.value = pretty_format(values)


def standard_format_config(config):
    """Standardise any degenerate representations e.g. namelist repeats."""
    for keylist, node in config.walk():
        if len(keylist) == 2:
            scheme, option = keylist
            if ":" in scheme:
                scheme = scheme.split(":", 1)[0]
            try:
                scheme_module = getattr(rose.formats, scheme)
                standard_format = getattr(scheme_module, "standard_format")
            except AttributeError:
                continue
            values = rose.variable.array_split(node.value, ",")
            node.value = standard_format(values)


def get_metadata_for_config_id(setting_id, meta_config):
    """Return a dict of metadata properties and values for a setting id."""
    metadata = {}
    search_id = REC_ID_STRIP_DUPL.sub("", setting_id)
    no_modifier_id = REC_MODIFIER.sub("", search_id)
    if no_modifier_id != search_id:
        # There is a modifier e.g. namelist:foo{bar}.
        node = meta_config.get([no_modifier_id], no_ignore=True)
        # Get metadata for namelist:foo
        if node is not None:
            metadata.update(dict([(o, n.value) for o, n
                                    in node.value.items()]))
            if rose.META_PROP_TITLE in metadata:
                metadata.pop(rose.META_PROP_TITLE)
            if (setting_id != search_id and
                rose.META_PROP_DUPLICATE in metadata):
                # foo{bar}(1) cannot inherit duplicate from foo.
                metadata.pop(rose.META_PROP_DUPLICATE)
    node = meta_config.get([search_id], no_ignore=True)
    # If modifier, get metadata for namelist:foo{bar}
    if node is not None:
        metadata.update(dict([(o, n.value) for o, n
                               in node.value.items()]))
    if search_id != setting_id and rose.META_PROP_TITLE in metadata:
        # Individual items of an array should not steal its title
        metadata.pop(rose.META_PROP_TITLE)
    metadata.update({'id': setting_id})
    return metadata


def run_macros(app_config, meta_config, config_name, macro_names,
               opt_conf_dir=None, opt_fix=False,
               opt_non_interactive=False, opt_output_dir=None,
               opt_validate_all=False, opt_quietness=False):
    """Run standard or custom macros for a configuration."""
        
    macro_tuples, modules = get_macros_for_config(
                  app_config, opt_conf_dir,
                  return_modules=True,
                  include_system=True)

    # Add all validator macros to the run list if specified.
    if opt_validate_all:
        for module_name, class_name, method, help in macro_tuples:
            if method == VALIDATE_METHOD:
                macro_name = ".".join([module_name, class_name])
                macro_names.insert(0, macro_name)
        if not macro_names:
            sys.exit(0)
    elif opt_fix:
        for module_name, class_name, method, help in macro_tuples:
            if module_name != rose.macros.__name__:
                continue
            if method == TRANSFORM_METHOD:
                macro_name = ".".join([module_name, class_name])
                macro_names.insert(0, macro_name)
        if not macro_names:
            sys.exit(0)
    # List all macros if none are given.
    if not macro_names:
        for module_name, class_name, method, help in macro_tuples:
            macro_name = ".".join([module_name, class_name])
            macro_id = MACRO_OUTPUT_ID.format(method.upper()[0], config_name,
                                              macro_name)
            if opt_quietness:
                print macro_id
            else:
                print macro_id
                for help_line in help.split("\n"):
                    print MACRO_OUTPUT_HELP.format(help_line)
        sys.exit(0)
    
    # Categorise macros given as arguments.
    macros_by_type = {}
    macros_not_found = [m for m in macro_names]
    for module_name, class_name, method, help in macro_tuples:
        this_macro_name = ".".join([module_name, class_name])
        if this_macro_name in macro_names:
            macros_by_type.setdefault(method, [])
            macros_by_type[method].append(this_macro_name)
            macros_not_found.remove(this_macro_name)
    for macro_name in macros_not_found:
        sys.stderr.write(ERROR_MACRO_NOT_FOUND.format(macro_name))
        RC = 1
    RC = 0
    
    # Run any validator macros.
    if VALIDATE_METHOD in macros_by_type:
        config_problem_dict = validate_config(app_config, meta_config,
                                              macros_by_type[VALIDATE_METHOD],
                                              modules,
                                              macro_tuples)
        if config_problem_dict:
            RC = 1
            if not opt_quietness:
                problem_macros = config_problem_dict.keys()
                problem_macros.sort()
                for macro_name in problem_macros:
                    problem_list = config_problem_dict[macro_name]
                    sort = rose.config.sort_settings
                    
                    problem_list.sort(lambda x, y: cmp(x.option, y.option))
                    problem_list.sort(lambda x, y: sort(x.section, y.section))
                    method_id = VALIDATE_METHOD.upper()[0]
                    macro_id = MACRO_OUTPUT_ID.format(method_id, config_name,
                                                      macro_name)
                    warnings = []
                    problems = []
                    for rep in problem_list:  # MacroReport instance
                        if rep.is_warning:
                            warnings.append(rep)
                            continue
                        problems.append(rep)
                    header = MACRO_OUTPUT_VALIDATE_ISSUES
                    header = header.format(macro_id, len(problems))
                    sys.stderr.write(header)
                    for rep in problems:
                        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                                   rep.value, rep.info)
                        sys.stderr.write(out)
                    if warnings:
                        header = MACRO_OUTPUT_WARNING_ISSUES
                        header = header.format(macro_id, len(warnings))
                        sys.stderr.write(header)
                    for rep in warnings:
                        out = PROBLEM_ENTRY.format(rep.section, rep.option,
                                                   rep.value, rep.info)
                        sys.stderr.write(out)

    # Run any transform macros.
    if TRANSFORM_METHOD in macros_by_type:
        _run_transform_macros(macros_by_type[TRANSFORM_METHOD],
                              config_name, app_config, meta_config, modules,
                              macro_tuples,
                              opt_non_interactive=opt_non_interactive,
                              opt_conf_dir=opt_conf_dir,
                              opt_output_dir=opt_output_dir)
    sys.exit(RC)


def _run_transform_macros(macros, config_name, app_config, meta_config,
                          modules, macro_tuples, opt_non_interactive=False,
                          opt_conf_dir=None, opt_output_dir=None):
    for transformer_macro in macros:
        user_allowed_changes = False
        macro_config = copy.deepcopy(app_config)
        new_config, change_list = transform_config(macro_config,
                                                   meta_config,
                                                   transformer_macro,
                                                   modules, macro_tuples)
        method_id = TRANSFORM_METHOD.upper()[0]
        macro_id = MACRO_OUTPUT_ID.format(method_id, config_name,
                                          transformer_macro)
        _handle_transform(app_config, new_config, change_list, macro_id,
                          opt_conf_dir, opt_output_dir, opt_non_interactive)


def _handle_transform(app_config, new_config, change_list, macro_id,
                      opt_conf_dir, opt_output_dir, opt_non_interactive):
    changes = []
    warnings = []
    user_allowed_changes = False
    for rep in change_list:  # MacroReport instance
        if rep.is_warning:
            warnings.append(rep)
        else:
            changes.append(rep)
    for reps, header, out in [(changes, MACRO_OUTPUT_TRANSFORM_CHANGES,
                               SETTING_ID),
                              (warnings, MACRO_OUTPUT_WARNING_ISSUES,
                               SETTING_ID)]:
        if not reps:
            continue
        sys.stdout.write(header.format(macro_id, len(reps)))
        for rep in reps:  # MacroReport instances
            this_out = out.format(
                        rep.section, rep.option, rep.value, rep.info)
            sys.stdout.write(this_out + "\n")
    if not opt_non_interactive and changes:
        user_allowed_changes = _get_user_accept()
    else:
        user_allowed_changes = False
    if user_allowed_changes or opt_non_interactive:
        app_config = new_config
        dump_config(app_config, opt_conf_dir, opt_output_dir)
            

def _get_user_accept():
    try:
        user_input = raw_input(PROMPT_ACCEPT_CHANGES)
    except EOFError:
        user_allowed_changes = False
    else:
        user_allowed_changes = (user_input == PROMPT_OK)
    return user_allowed_changes


def dump_config(app_config, opt_conf_dir, opt_output_dir=None):
    pretty_format_config(app_config)
    if opt_output_dir is None:
        directory = opt_conf_dir
    else:
        directory = opt_output_dir
    file_path = os.path.join(directory, rose.SUB_CONFIG_NAME)
    rose.config.dump(app_config, file_path)


def parse_macro_mode_args(mode="macro", argv=None):
    """Parse options/arguments for rose macro and upgrade."""
    opt_parser = RoseOptionParser()
    options = ["conf_dir", "meta_path", "non_interactive", "output_dir"]
    if mode == "macro":
        options.extend(["fix", "validate_all"])
    elif mode == "upgrade":
        options.extend(["downgrade"])
    else:
        raise KeyError("Wrong mode: {0}".format(mode))
    opt_parser.add_my_options(*options)
    if argv is None:
        opts, args = opt_parser.parse_args()
    else:
        opts, args = opt_parser.parse_args(argv)
    opts, args = opt_parser.parse_args(argv)
    if mode == "upgrade" and len(args) > 1:
        sys.stderr.write(parser.get_usage())
        return None
    if opts.conf_dir is None:
        opts.conf_dir = os.getcwd()
    sys.path.append(os.getenv("ROSE_HOME"))
    add_opt_meta_paths(opts.meta_path)
    config_name = os.path.basename((os.path.abspath(opts.conf_dir)))
    config_file_path = os.path.join(opts.conf_dir,
                                    rose.SUB_CONFIG_NAME)
    if (not os.path.exists(config_file_path) or
        not os.path.isfile(config_file_path)):
        sys.stderr.write(ERROR_LOAD_CONFIG_DIR.format(opts.conf_dir))
        return None
    # Load the configuration and the metadata macros.
    config_loader = rose.config.ConfigLoader()
    app_config = config_loader(config_file_path)
    standard_format_config(app_config)

    # Load meta config if it exists.
    meta_config = None
    meta_path, warning = load_meta_path(app_config, opts.conf_dir)
    if meta_path is None:
        if mode == "macro":
            text = ERROR_LOAD_METADATA.format("")
            if warning:
                text = warning
            sys.stderr.write(text)
            return None
    else:
        meta_config_path = os.path.join(meta_path, rose.META_CONFIG_NAME)
        if os.path.isfile(meta_config_path):
            meta_config = config_loader.load_with_opts(meta_config_path)
    return app_config, meta_config, config_name, args, opts


def _report_error(exception=None, text=""):
    """This will be replaced by rose.reporter utilities."""
    if text:
        text += "\n"
    if exception is not None:
        text += type(exception).__name__ + ": " + str(exception) + "\n"
    sys.stderr.write(text + "\n")


def main():
    """Run rose macro."""
    add_site_meta_paths()
    add_env_meta_paths()
    return_objects = parse_macro_mode_args()
    if return_objects is None:
        sys.exit(1)
    app_config, meta_config, config_name, args, opts = return_objects
    run_macros(app_config, meta_config, config_name, args,
               opts.conf_dir, opts.fix,
               opts.non_interactive, opts.output_dir,
               opts.validate_all, opts.quietness)
               

if __name__ == "__main__":
    main()
