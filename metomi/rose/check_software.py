# Copyright (C) British Crown (Met Office) & Contributors.
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
"""NAME
    rose check-software

SYNOPSIS
    rose check-software [OPTIONS]

DESCRIPTION
    Check software dependencies for the rose documentation builder.

OPTIONS
    --doc   Only check dependencies for the documentation builder.
    --rst   Output dependencies as text in rst format."""

import re
from subprocess import Popen, PIPE
import sys


TARGET_REGEX = r'\<(.*)\>'


def get_terminal_width(default_width, min_width):
    """Return the terminal width.

    Return:
        int - terminal width OR min_width if width < min_width ELSE min_width.
    """
    proc = Popen(['stty', 'size'], stdout=PIPE)
    if proc.wait():
        return default_width
    else:
        try:
            return max(
                min_width, int(proc.communicate()[0].split()[1]))
        except IndexError:
            return default_width


TERM_WIDTH = get_terminal_width(80, 60)
DEP_NOT_FOUND = 'DEP_NOT_FOUND'


def version_tuple(version_string):
    """Return a tuple of version components suitable for comparison.

    Splits versions on '.' characters and attempts to convert each component to
    an integer.
    """
    version_list = []
    for component in version_string.strip().split('.'):
        try:
            version_list.append(int(component))
        except ValueError:
            version_list.append(component)
    return tuple(version_list)


def version_str(version_tup):
    """Converts a version tuple back into a regular string."""
    return '.'.join(str(x) for x in version_tup)


def cmd_exists(command):
    """Returns True if provided shell command is present (`which` wrapper)."""
    if Popen(['which', command], stdout=PIPE, stderr=PIPE).wait():
        return False
    return True


def cmd_version(command, command_template='--version',
                version_template=r'(.*)', outfile=1):
    """Return the version number of a provided shell command.

    Args:
        command (str): The name of the command to check.
        command_template (str): The command line argument required to extract
            the version number from the script (e.g. --version).
        version_template (str): Regex to extract the version from the returned
            string.
        outfile (int): The filenumber that the version output is written to
            (e.g. 1 for stdout, 2 for stderr).

    Return: str or None if version cannot be determined or DEP_NOT_FOUND
            if the command is not present at all.
    """
    if not cmd_exists(command):
        return DEP_NOT_FOUND
    if not isinstance(command_template, list):
        command_template = [command_template]
    output = Popen([command] + command_template, stdout=PIPE,
                   stderr=PIPE, text=True).communicate()[outfile - 1].strip()
    try:
        return re.search(version_template, output).groups()[0]
    except AttributeError:
        return None


def shell_command(_, shell=None, version_template=r'(.*)', outfile=1):
    output = Popen(shell, stdout=PIPE, text=True).communicate()[outfile - 1]
    try:
        return re.search(version_template, output).groups()[0]
    except AttributeError:
        return None


def py_version(module, attr_name='__version__'):
    """Return the version of the provided python module.

    Args:
        module (str): The name of the python module.
        attr_name (str): The name of the "version" attribute.

    Returns:
        str - The version number if the module is found, None if the version
        cannot be determined and DEP_NOT_FOUND if the module is not found.
    """
    try:
        imported_module = __import__(module)
    except (ImportError, RuntimeError):
        return DEP_NOT_FOUND
    try:
        version = getattr(imported_module, attr_name)
        if isinstance(version, tuple):
            return version_str(version)
        return version
    except AttributeError:
        return None


# List of functions for obtaining version types - default is cmd_version.
VERSION_CHECKERS = {'py': py_version, 'cmd': shell_command}


def dep_str(min_version=None, min_incompat_version=None):
    version_repr = ''
    if min_incompat_version:
        if min_version:
            version_repr = '%s+, <%s' % (version_str(min_version),
                                         version_str(min_incompat_version))
        else:
            version_repr = '<%s' % (version_str(min_version))
    elif min_version:
        version_repr = '%s+' % version_str(min_version)
    return version_repr


def process_dependency(dependency):
    """Process prefix (py:) and target (foo<bar>) from a dependency string.

    Return:
        tuple - (prefix, dependency_name, dependency, version_checker)
            - prefix (str) - Dependency domain (e.g. python module 'py').
            - dependency_name (str) - Dependency with prefix stripped.
              This is the target if provided e.g. bar for `foo<bar>`.
            - dependency (str) - Full dependency name with prefix.
              This is the alt if a target if provided e.g. foo for `foo<bar>`.
            - version_checker (callable) - Function for acquiring version
              string.
    """
    # Process dependency prefix (e.g. "py:sphinx").
    if ':' in dependency:
        prefix, dependency_name = dependency.split(':')
        version_checker = VERSION_CHECKERS[prefix]
        if prefix == 'cmd':
            # The "cmd" prefix should not be displayed.
            dependency = dependency_name
    else:
        dependency_name = dependency
        version_checker = cmd_version
        prefix = ''

    # Process dependecy target (e.g. "dot<graphviz>").
    if '<' in dependency_name:
        dependency = re.sub(TARGET_REGEX, '', dependency).strip()
        dependency_name = re.search(TARGET_REGEX, dependency_name).groups()[0]

    return prefix, dependency_name, dependency, version_checker


def check(dependency, min_version=None, min_incompat_version=None, **kwargs):
    """Evaluate the provided dependency.

    Args:
        dependency (str): The name of the dependency to evaluate.
            Dependency should be prefixed as appropriate (e.g. 'py:' for a
            python module.
        min_version (tuple): A version tuple - dependency interpreted as
            "version >= min_version".
        min_incompat_version (tuple): A version tuple - dependency
            interpreted as "version < min_incompat_version".
        **kwargs (dict): Any options to be passed to the version checker.

    Returns:
        list - List of tuples of the form (message, result).
    """
    # Determine version checker.
    prefix, dependency_name, dependency, version_checker = process_dependency(
        dependency)

    # Generate output message.
    line = dependency
    version_repr = dep_str(min_version, min_incompat_version)
    if version_repr:
        line += ' (%s)' % version_repr
    line += ' ' + '.' * (TERM_WIDTH - len(line) - 25) + ' '

    # Get version number.
    version_string = version_checker(dependency_name, **kwargs)
    if version_string == DEP_NOT_FOUND:
        return (line + 'not ok (not found)', False)

    # If version not determinable.
    if not version_string:
        if min_version:
            return (line + 'not ok (unknown version)', False)
        return (line + 'ok (unknown version)', True)

    # Check version < min_incompat_version.
    version = version_tuple(version_string)
    if min_incompat_version and version > min_incompat_version:
        return (line + 'not ok (%s > %s)' % (
            version_string, version_str(min_incompat_version)), False)

    # Check version >= min_version.
    if min_version:
        if version >= min_version:
            return (line + 'ok (%s)' % version_string, True)
        else:
            return (line + 'not ok (%s < %s)' % (
                version_string, version_str(min_version)), False)

    return (line + 'ok (%s)' % version_string, True)


def check_all(name, dep_list):
    """Evaluate the provided list of dependencies.

    Args:
        name (str): The name of the group of dependencies.
        dep_list (list): List of tuples as returned by `check`.

    Returns:
        bool - True if all checks passed, False otherwise.
    """
    print(name)
    if len(dep_list[0]) == 2:
        print('-' * len(name))
        # Performing dependency checking.
        for msg, _ in dep_list:
            print(msg)
        if all(result for _, result in dep_list):
            print('Result: PASS\n')
            return True
        else:
            print('Result: FAIL\n')
            return False
    else:
        # Outputting dependency list for documentation.
        for msg in dep_list:
            print('   %s' % msg)
        print()


def check_software(check=check):
    """Check required and optional dependencies."""
    ret = check_all('Required Software', [
        check('python3', (3, 6), version_template=r'Python (.*)'),
        check('cylc', (8,)),
        check('py:jinja2'),
        check('py:aiofiles')
    ])

    check_all('Rosie', [
        check('py:tornado', (3, 0), attr_name='version'),
        check('py:requests', (2, 2, 1)),
        check('py:sqlalchemy', (0, 9)),
        check('svn', (1, 8), command_template=['--version', '--quiet']),
        check('fcm', version_template=r'FCM ([\d\.\-]+)'),
        check('cmd:perl', (5, 10, 1),
              shell=['perl', '-e', 'print(substr($^V, 1))'])
    ])

    tutorial(check=check)
    docs(check=check)
    return ret


def tutorial(check=check):
    """Check software dependencies for the Cylc/Rose tutorial."""
    ret = check_all('Tutorial', [
        check('py:pillow <PIL>')
    ])

    return ret


def docs(check=check):
    """Check software dependencies for the documentation builder."""
    ret = check_all('Documentation Builder', [
        check('py:sphinx', (1, 5, 3)),
        check('py:sphinx_rtd_theme', (0, 2, 4)),
        check('py:sphinxcontrib.httpdomain'),
        check('py:hieroglyph')
    ])

    check_all('Documentation Builder - Recommended Extras', [
        check('rsvg', version_template=r'rsvg version (.*)'),
        check(
            'py:sphinxcontrib.svg2pdfconverter <sphinxcontrib.rsvgconverter>'
        )
    ])

    check_all('Documentation Builder - PDF Dependencies', [
        check('tex', version_template=r'TeX ([^\s]+)'),
        check('latexmk', version_template=r'Version (.*)'),
        check('pdflatex', version_template=r'pdfTeX .*-.*-([^\s]+)')
    ])

    check_all('Documentation Builder - Linkcheck Dependencies', [
        check('py:requests')
    ])

    return ret


def echo(dependency, min_version=None, min_incompat_version=None, **kwargs):
    """Return dependency repr in rst - Standin for the check() method."""
    dependency = process_dependency(dependency)[2]

    ret = '* %s' % dependency
    if min_version or min_incompat_version:
        ret += ' - *%s*' % dep_str(min_version, min_incompat_version)
    return ret


def main():
    if '--help' in sys.argv:
        # Print help and exit.
        print(__doc__)
    elif '--rst' in sys.argv:
        # Print dependencies in RST format and exit.
        sys.exit(0 if check_software(check=echo) else 1)
    elif any(arg in sys.argv for arg in ['--doc', '--docs']):
        sys.exit(0 if docs() else 1)
    else:
        # Check software dependencies, report and exit.
        check_software()
