# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# (C) British Crown Copyright 2012-7 Met Office.
#
# This file is part of Rose, a framework for meteorological suites.
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
# -----------------------------------------------------------------------------
"""The rose domain is for documenting rose configurations and built-in
applications.

Rose Objects:
    The rose domain supports the following object types:

    * Applications using the prefix ``app`` (i.e. ``rose:app``).
    * Configuration files using the prefix ``file`` (i.e. ``rose:file``).
    * Configuration sections using the prefix ``conf`` (i.e. ``rose:conf``).
    * Configuration settings using the prefix ``conf`` (i.e. ``rose:conf``).

    See the corresponding directives for more information on each object type.

Reference Syntax:
    Once documented objects can be referenced using the following syntax:

    ``:rose:CONFIG-FILE.[parent-section]child-config``

    Where ``CONFIG-FILE`` is:

    * ``APP-NAME`` for applications (e.g. ``fcm_make``).
    * ``FILE-NAME`` for configuration files (e.g. ``rose.conf``).

Referencing From RST Files:
    To reference a rose object add the object ``TYPE`` into the domain
    (e.g. ``conf`` or ``app``).

    .. code-block:: rst

       :rose:TYPE:`CONFIG-FILE.[parent-section]child-config`

    e.g:

    .. code-block:: rst

       * :rose:app:`fcm_make`
       * :rose:conf:`fcm_make.args`

Example:
    .. code-block:: rst

       .. rose:file:: rose-suite.conf

          The config file used for configuring suite level settings.

          .. rose:conf:: jinja2:suite.rc

             A section for specifying Jinja2 settings for use in the ``suite.rc``
             file.

             Note that one ommits the square brackets for config sections, if
             :rose:conf: contains other :rose:conf:`s then it is implicitly a
             section and the brackets are added automatically. If you wish to
             document a section which contains no settings write it using
             square brackets.

             .. rose:conf:: ROSE_VERSION

                Provide the intended rose version to the suite.

                .. deprecated:: 6.1.0

                   No longer required, this context is now provided internally.

"""

import re

from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.directives import ObjectDescription
from sphinx.roles import XRefRole
from sphinx.util.nodes import make_refnode
from sphinx.util import logging
from sphinx.util.docfields import Field, TypedField

logger = logging.getLogger(__name__)

ROSE_DOMAIN_REGEX = re.compile(
   r'rose:(\w+):'    # Rose domain prefix + object type.
   r'([^\|\[ \n]+)'  # Configuration file.
   r'(\[.*\])?'      # Configuration section.
   r'(?:\|?(.*))?'   # Configuration setting.
)
SECTION_REGEX = re.compile(r'(\[.*\])(.*)')
OPT_ARG_REGEX = re.compile(r'=([^\]]+)?$', flags=re.M)

def tokenise_namespace(namespace):
    """Convert a namespace string into a list of tokens.

    Tokens are (domain, name) tuples.

    Examples:
        # Partial namespaces.
        >>> tokenise_namespace('rose:conf:foo')
        [('rose:conf', 'foo')]
        >>> tokenise_namespace('rose:conf:[foo]')
        [('rose:conf', '[foo]')]
        >>> tokenise_namespace('rose:conf:[foo]bar')
        [('rose:conf', '[foo]'), ('rose:conf', 'bar')]

        # Full namespaces.
        >>> tokenise_namespace('rose:app:foo')
        [('rose:app', 'foo')]
        >>> tokenise_namespace('rose:file:foo.conf')
        [('rose:file', 'foo.conf')]
        >>> tokenise_namespace('rose:conf:foo|bar')
        [('rose:app', 'foo'), ('rose:conf', 'bar')]
        >>> tokenise_namespace('rose:conf:foo[bar]')
        [('rose:app', 'foo'), ('rose:conf', '[bar]')]
        >>> tokenise_namespace('rose:conf:foo[bar]baz')
        [('rose:app', 'foo'), ('rose:conf', '[bar]'), ('rose:conf', 'baz')]
        >>> tokenise_namespace('rose:conf:foo.conf[bar:pub]baz')
        [('rose:file', 'foo.conf'), ('rose:conf', '[bar:pub]'), ('rose:conf', 'baz')]
    """
    match = ROSE_DOMAIN_REGEX.match(namespace)

    domain = ':'.join(namespace.split(':')[2:])

    if not match:
        # Namespace is only partial, return it as a single configuration token.
        section, setting = SECTION_REGEX.match(domain).groups()
        ret = [('rose:conf', section)]
        if setting:
            ret.append(('rose:conf', setting))
        return ret

    typ, conf_file, conf_section, setting = match.groups()

    if typ == 'conf' and not (conf_section or setting):
        # Namespace is only partial, return it as a single configuration token.
        return [(('rose:conf'), domain)]

    if typ in ['file', 'app']:
        ret = [('rose:%s' % typ, conf_file)]
    elif '.' in conf_file:
        # Must be a rose config file.
        ret = [('rose:file', conf_file)]
    else:
        # Must be a rose application.
        ret = [('rose:app', conf_file)]

    if conf_section:
       ret.append(('rose:conf', conf_section))
    if setting:
       ret.append(('rose:conf', setting))

    return ret


def namespace_from_tokens(tokens):
    """Convert a list of tokens into a string namespace.

    Tokens are (domain, name) tuples.

    Examples:
       >>> namespace_from_tokens([('rose:app', 'foo')])
       'rose:app:foo'
       >>> namespace_from_tokens([('rose:file', 'foo')])
       'rose:file:foo'
       >>> namespace_from_tokens([('rose:app', 'foo'), ('rose:conf', 'bar')])
       'rose:conf:foo|bar'
       >>> namespace_from_tokens([('rose:app', 'foo'), ('rose:conf', '[bar]')])
       'rose:conf:foo[bar]'
       >>> namespace_from_tokens([('rose:app', 'foo'), ('rose:conf', '[bar]'),
       ...                        ('rose:conf', 'baz')])
       'rose:conf:foo[bar]baz'
       >>> namespace_from_tokens([('rose:file', 'foo.conf'),
       ...                        ('rose:conf', '[bar]'),
       ...                        ('rose:conf', 'baz')])
       'rose:conf:foo.conf[bar]baz'
    """
    ret = tokens[-1][0] + ':'
    previous_domain = None
    for domain, name in tokens:
        # Root level configuration files.
        if domain in ['rose:app', 'rose:file']:
            if previous_domain:
                # App must be a root domain.
                logger.warning('Invalid tokens "%s"' % tokens)
                return False
            else:
                ret += name

        # Rose configuration.
        elif domain == 'rose:conf':
            if previous_domain in ['rose:app', 'rose:file']:
                if name.startswith('['):
                   # section requires no separator
                   ret += name
                else:
                   # Setting requires `|` separator.
                   ret += '|%s' % name
            elif previous_domain == 'rose:conf':
                # Setting requires no separator if following a section.
                ret += name
            else:
                logger.warning('Invalid tokens "%s"' % tokens)
                return False
        else:
            logger.warning('Invalid tokens "%s"' % tokens)
            return False
        previous_domain = domain
    return ret


class RoseDirective(ObjectDescription):
    """Base class for implementing rose objects.

    Subclasses must provide:
        - NAME

    Subclasses can provide:
        - LABEL
        - ARGUMENT_SEPARATOR
        - ALT_FORM_SEPARATOR
        - ALT_FORM_TEMPLATE
        - doc_field_types - List of ``Field`` objects for object parameters.
        - run() - For adding special rev_context variables via add_rev_context.
        - handle_signature() - For changing the display of objects.
        - custom_name_template - String template accepting one string format
          argument for custom formatting the node name (e.g. ``'[%s]'`` for conf
          sections.

    ref_context Variables:
        Sphinx domains use ``ref_context`` variables to determine the
        relationship between objects. E.g. for a rose app the ``rose:app``
        variable is set to the name of the app. This variable will be made
        available to all children which is how they determine that they belong
        to the app.

        * Variables set in ``run()`` are available to this object along with
          all of its children.
        * Variables set in ``before_content()`` are only available to children.
        * All variables set via ``add_ref_context()`` will be automatically
          removed in ``after_content()`` to prevent leaking scope.
    """

    allow_nesting = False
    """Override in settings which are permitted to be nested (e.g. 'conf')."""

    NAME = None
    """The rose domain this directive implements see RoseDomain.directives"""
    LABEL = ''
    """Label to prepend to objects."""
    ARGUMENT_SEPARATOR = '='
    """String for splitting the directive argument into a name and a suffix."""
    ALT_FORM_SEPARATOR = '&'
    """String for splitting alternate names."""
    ALT_FORM_TEMPLATE = '(alternate: %s)'
    """String template for writing out alternate names. Takes one string format
    argument."""

    ROSE_CONTEXT = 'rose:%s'
    """Prefix for all rose ref_context variables."""

    def __init__(self, *args, **kwargs):
        self.ref_context_to_remove = []  # Cannot do this in run().
        ObjectDescription.__init__(self, *args, **kwargs)

    def run(self):
        # Automatically generate the "rose:NAME" ref_context variable.
        self.add_ref_context(self.NAME)
        index_node, cont_node = ObjectDescription.run(self)

        # Add a marker on the output node so we can determine the context
        # namespace later (see RoseDomain.resolve_xref).
        context_var = self.ROSE_CONTEXT % self.NAME
        cont_node.ref_context = {context_var: self.process_name(
            self.arguments[0].strip())[0]}

        return [index_node, cont_node]

    def add_ref_context(self, key):
        """Add a new ``ref_context`` variable.

        * The variable will be set to the name of the object.
        * The variable will be automatically removed in ``after_content()``
          to prevent leaking scope.

        Args:
            key (str): The name for the new variable without the ``rose:``
                prefix.
        """
        ref_context = self.state.document.settings.env.ref_context
        context_var = self.ROSE_CONTEXT % key
        ref_context[context_var] = (
            self.process_name(self.arguments[0].strip())[0])
        self.ref_context_to_remove.append(key)

    def remove_ref_context(self, key):
        """Remove a ``ref_context`` variable.

        Args:
            key (str): The name of the variable to remove without the
                ``rose:`` prefix.
        """
        ref_context = self.state.document.settings.env.ref_context
        context_var = self.ROSE_CONTEXT % key
        if ref_context.get(context_var) == (
                self.process_name(self.arguments[0].strip())[0]):
            del ref_context[context_var]

    def get_ref_context(self, key):
        """Return the value of a ``ref_context`` variable.

        Args:
            key (str): The name of the variable without the ``rose:`` prefix.

        Return:
            The value of the context variable, if set via ``add_ref_context()``
            this will be the name of the object which set it.
        """
        ref_context = self.state.document.settings.env.ref_context
        return ref_context.get(self.ROSE_CONTEXT % key)

    def after_content(self):
        """This method is called after child objects have been processed.
        
        There is also the ``before_content()`` method which is called during
        ``run()`` before child objects have been processed but after the
        current object has been processed.
        """
        for context_var in self.ref_context_to_remove:
            self.remove_ref_context(context_var)
        ObjectDescription.after_content(self)

    def process_name(self, name):
        """Perform standard pre-processing of a node name.

        * Process argument strings (e.g. ``bar`` in ``foo=bar``).
        * Process alternate forms (e.g. ``bar`` in ``foo & bar``).
        * Process custom name templates.

        Return:
            tuple - (name, argument, alt_forms)
                - name (str) - The processed name with everything else
                  stripped.
                - argument (str) - Any specified argument string else ''.
                - alt_forms (list) - List of strings containing alternate names
                  for the node.
        """
        alt_forms = []
        if self.ALT_FORM_SEPARATOR:
            ret = name.split(self.ALT_FORM_SEPARATOR)
            name = ret[0].strip()
            alt_forms = [x.strip() for x in ret[1:]]

        # Separate argument strings (e.g. foo=FOO).
        argument = ''
        if self.ARGUMENT_SEPARATOR:
            try:
                name, argument = name.split(self.ARGUMENT_SEPARATOR)
            except ValueError:
                pass

        # Apply custom name template if specified.
        if hasattr(self, 'custom_name_template'):
            name = self.custom_name_template % name

        return name, argument, alt_forms
        
    def handle_signature(self, sig, signode, display_text=None):
        """This method determines the appearance of the object.
        
        Overloaded Args:
            display_test: Used for overriding the object name.
        """
        # Override sig with display_text if provided.
        if display_text is None:
            display_text = sig

        display_text, argument, alt_forms = self.process_name(display_text)

        # Add a label before the name of the object.
        signode += addnodes.desc_annotation(*('%s ' % self.LABEL,) * 2)
        # Add the object name.
        signode += addnodes.desc_name(sig, display_text)
        # Add arguments.
        if argument:
            argument = '%s %s' % (self.ARGUMENT_SEPARATOR, argument)
            signode += addnodes.desc_annotation(argument, argument)
        # Add alternate object names.
        if alt_forms:
            signode += addnodes.desc_annotation(
                *(self.ALT_FORM_TEMPLATE % (', '.join(alt_forms)),) * 2)

        signode['fullname'] = sig
        return (sig, self.NAME, sig)

    def needs_arglist(self):
        return False

    def add_target_and_index(self, name_cls, sig, signode):
        """This method handles namespacing."""
        name = self.process_name(name_cls[0])[0]

        # Get the current context in tokenised form.
        context_tokens = []
        ref_context = self.state.document.settings.env.ref_context
        for key in ['app', 'file', 'conf-section', 'conf']:
            token = self.ROSE_CONTEXT % key
            if token in ref_context:
                value = ref_context[token]
                if key == 'conf-section':
                    token = self.ROSE_CONTEXT % 'conf'
                new_token = (token, value)
                if new_token not in context_tokens:
                    context_tokens.append(new_token)

        # Add a token representing the current node.
        new_token = (self.ROSE_CONTEXT % self.NAME, name)
        if new_token not in context_tokens:
            context_tokens.append(new_token)

        # Generate a namespace from the tokens.
        namespace = namespace_from_tokens(context_tokens)
        if namespace is False:
            logger.error('Invalid namespace for rose object "%s"' % namespace,
                         location=signode)

        # Register this namespace.
        signode['ids'].append(namespace)
        self.env.domaindata['rose']['objects'][namespace] = (
            self.env.docname, '')

    def get_index_text(self, modname, name):
        return ''


class RoseAppDirective(RoseDirective):
    """Directive for documenting rose apps.

    Example:

        Click :guilabel:`source` to view source code.

        .. code-block:: rst

           .. rose:app:: foo

              An app called ``foo``.

    """

    NAME = 'app'
    LABEL = 'Rose App'


class RoseFileDirective(RoseDirective):
    """Directive for documenting rose apps.

    Example:

        Click :guilabel:`source` to view source code.

        .. code-block:: rst

           .. rose:file:: foo

              An configuration file called ``foo``.

    """

    NAME = 'file'
    LABEL = 'Rose Configuration'


class RoseConfigDirective(RoseDirective):
    """Directive for documenting config sections.

    Optional Attributes:
        * ``envvar`` - Associate an environment variable with this
          configuration option.
        * ``compulsory`` - Set to ``True`` for compulsory settings, ommit this
          field for optional settings.

    Additional ref_context:
        * ``rose:conf-section`` - Set for parent configurations, is available to
          any child nodes.

    Example:

        Click :guilabel:`source` to view source code.

        .. code-block:: rst

           .. rose:conf:: foo

              :default: foo
              :opt argtype foo: Description of option ``foo``.
              :opt bar: Description of bar

              A setting called ``foo``.

           .. rose:conf:: bar

              A section called ``bar``.

              .. rose:conf:: baz

                 :compulsory: True
                 :env: AN_ASSOCIATED_ENVIRONMENT_VARIABLE

                 A config called ``[bar]baz``.
    """
    NAME = 'conf'
    LABEL = 'Config'
    SECTION_REF_CONTEXT = 'conf-section'
    ARGUMENT_SEPARATOR = '='

    # Add custom fields.
    doc_field_types = [
        # NOTE: The field label must be sort to avoid causing a line break.
        Field('envvar', label='Env Var', has_arg=False, names=('env',),
              bodyrolename='obj'),
        Field('compulsory', label='Compulsory', has_arg=True,
              names=('compulsory',)),
        Field('default', label='Default', has_arg=False, names=('default',)),
        TypedField('option', label='Options', names=('opt',),
                   typerolename='obj', typenames=('paramtype', 'type'),
                   can_collapse=True)
    ]

    def run(self):
        """Overridden to add the :rose:conf-section: ``ref_context`` variable
        for nested sections."""
        if any('.. rose:conf::' in line for line in self.content):
            # This configuration contains other configurations i.e. it is a
            # configuration section. Apply a custom_name_template so that it is
            # written inside square brackets.
            self.custom_name_template = '[%s]'
            # Sections cannot be written with argument examples.
            self.ARGUMENT_SEPARATOR = None
            # Add a ref_context variable to mark this node as a config section.
            self.add_ref_context(self.SECTION_REF_CONTEXT)

        return RoseDirective.run(self)


class RoseXRefRole(XRefRole):
    """Handle references to rose objects.
    
    This should be minimal."""

    def process_link(self, env, refnode, has_explicit_title, title, target):
        if not has_explicit_title:
            pass
        return title, target


class RoseDomain(Domain):
    """Sphinx extension to add the ability to document rose objects.
    
    Example:

        Click :guilabel:`source` to view source code.

        .. code-block:: rst

           .. rose:app: foo

              An app called ``foo``.

              .. rose:conf: bar

                 A setting called ``bar`` for the app ``foo``.

              .. rose:conf: baz

                 A config section called ``baz`` for the app ``foo``.

                 .. rose:conf: pub

                    A config setting called ``[baz]pub`` for the app ``foo``.
    """

    name = 'rose'
    """Prefix for rose domain (used by sphinx)."""
    label = 'Rose'
    """Display label for the rose domain (used by sphinx)."""

    object_types = {
        'app': ObjType('app', 'app', 'obj'),
        'file': ObjType('file', 'file', 'obj'),
        'conf': ObjType('conf', 'conf', 'obj')
    }
    """List of object types, this should mirror ``directives``."""

    directives = {
        'app': RoseAppDirective,
        'file': RoseFileDirective,
        'conf': RoseConfigDirective
    }
    """List of domains associated with prefixes (e.g. ``app`` becomes the
    ``rose:app`` domain."""

    roles = {
        'app': RoseXRefRole(),
        'file': RoseXRefRole(),
        'conf': RoseXRefRole()
    }
    """Sphinx text roles associated with the domain. Text roles are required
    for referencing objects. There should be one role for each item in
    ``object_types``"""

    initial_data = {
        'objects': {}  # path: (docname, synopsis)
    }
    """This sets ``self.data`` on initialisation."""

    def clear_doc(self, docname):
        """Removes documented items from  the rose domain.
        
        Not sure why, but apparently necessary.
        """
        for fullname, (pkg_docname, _l) in list(self.data['objects'].items()):
            if pkg_docname == docname:
                del self.data['objects'][fullname]

    def get_objects(self):
        """Iterates through documented items in the rose domain."""
        for refname, (docname, type_) in list(self.data['objects'].items()):
            yield refname, refname, type_, docname, refname, 1

    @staticmethod
    def get_context_namespace(node):
        """Extract the namespace from a content node.
        
        Walks up the node hierarchy from the current node collecting
        ref_context information as it does. See ``RoseDirective.run`` for
        information on how this context comes to reside in the node.
        """
        context_namespace = []
        while hasattr(node, 'parent'):
            if hasattr(node, 'ref_context'):
                # Each ref_context dict should contain only one entry (for
                # now).
                context_namespace.append(node.ref_context.items()[0])
            node = node.parent
        context_namespace.reverse()
        return context_namespace

    def resolve_xref(self, env, fromdocname, builder, typ, target, node,
                     contnode):
        """Associate a reference with a documented object.
        
        The important parameters are:
            typ (str): The object type - see ``RoseDomain.object_types``.
            target (str): The rest of the reference as written in the rst.

        This implementation simplifies things by storing objects under their
        namespace which is the same syntax used to reference the objects i.e:

        .. rose:app: Foo

        Creates the entry ``self.data['objects']['rose:app:foo']``.

        Which can be referenced in rst by:

        .. code-block:: rst

           :rose:app:`foo`
        """
        if OPT_ARG_REGEX.search(target):
           # If target has a trailing argument ignore it.
           target = target.split('=')[0]

        # Determine the namespace of the object being referenced.
        if typ in ['app', 'file']:
            # Object is a root rose config - path is absolute.
            namespace = 'rose:%s:%s' % (typ, target)
        elif typ == 'obj':
            # Object is an 'obj' e.g. an environment variable, 'obj's are not
            # referenceable (yet).
            return None
        elif typ == 'conf':
            relative_to_conf = False
            if target.startswith('['):
                # Target is relative to the context conf_file.
                relative_to_conf = True

            # Get the referenced namespace in tokenised form.
            reference_namespace = tokenise_namespace(
                'rose:%s:%s' % (typ, target))
            if reference_namespace[0][0] in ['rose:app', 'rose:file']:
                # Target is a root rose config - path is absolute.
                namespace = 'rose:%s:%s' % (typ, target)
            else:
                # Target is not a root config - path is relative.
                context_namespace = self.get_context_namespace(node)
                if not context_namespace:
                    logger.warning(
                        'Relative reference requires local context "%s".' % (
                        target), location=node)
                    return
                if relative_to_conf:
                    # Target is relative to the context conf_file.
                    namespace_tokens = (context_namespace[:1] +
                                        reference_namespace)
                else:
                    # Target is relative to the current namespace.
                    namespace_tokens = (context_namespace[:-1] +
                                        reference_namespace)
                # Convert the tokenised namespace into a string namespace.
                namespace = namespace_from_tokens(namespace_tokens)

        # Lookup the object from the namespace.
        try:
            data = self.data['objects'][namespace]
        except KeyError:
            # No reference exists for "object_name".
            logger.warning('No Ref for "%s"' % namespace, location=node)
            return None

        # Create a link pointing at the object.
        return make_refnode(builder, fromdocname, data[0], namespace,
                            contnode, namespace)


def setup(app):
    app.add_domain(RoseDomain)
