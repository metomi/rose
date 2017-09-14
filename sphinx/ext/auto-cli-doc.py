"""An extension for auto-documenting command line interfaces."""

from __future__ import print_function

from collections import OrderedDict
import re
from subprocess import Popen, PIPE

from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.statemachine import ViewList
import sphinx
from sphinx.util.nodes import nested_parse_with_titles


# --- Generic regex'es. ---

# Splits the content of a documentation section by indentation.
INDENT_REGEX = re.compile(r'^([^\s\t].*)((?:\n(?![^\s]).*)+)', re.MULTILINE)
# Matches rst `literals`.
LITERAL_REGEX = re.compile(r'(?<!\`)\`(?!\`)([^\`]+)(?<!\`)\`(?!\`)')


# --- ReStructured Text properties. ---

# Standard re-structured-text indentation level.
RST_INDENT = '   '  # 3 spaces ( .. following sections must be flush with 'f').
# Characters used to underline rst headings in order of precedence.
RST_HEADING_CHARS = ['=', '-', '^', '"']


# --- Rose specific regex'es. ---

# Splits the documentation file into commands and their associated
# documentation.
ROSE_COMMAND_REGEX = re.compile(r'={%d}\n(.*)\n={%d}\n(((?!====).*\n)+)' %
                                (50, 50))
# Splits command documentation into sections and content.
ROSE_HELP_SECTION_REGEX = re.compile(r'(^(?:\w+\s?)+$)((?:\n(?!^\w).*)+)',
                                re.MULTILINE)


# --- Rose specific help section formatting. ---

# Documentation sections which should be rendered as mono-spaced plain-text.
ROSE_CODE_SECTIONS = {  # SECTION_NAME: SYNTAX_HIGHLIGHTING
    'EXAMPLES': 'bash',
}
# Documentation sections which contain lists of options (along with one or more
# un-formatted description lines at the start of the block).
ROSE_OPTION_SECTIONS = ['OPTIONS', 'ARGUMENTS', 'ENVIRONMENT VARIABLES',
                   'JINJA2 VARIABLES', 'CONFIGURATION']


def get_indentation(lines):
    """Return the minimum indentation of a collection of lines.

    Example:
        >>> get_indentation([
        ...     '    abc',
        ...     '     def',
        ...     '',
        ...     '   ghi'
        ... ])
        3
    """
    indentation = None
    contains_new_lines = False
    for line in lines:
        if not line:
            contains_new_lines = True
            continue
        count = 0
        for char in line:
            if char == ' ':
                count += 1
            else:
                break
        if not indentation or count < indentation:
            indentation = count
    if indentation is None and contains_new_lines:
        return 0
    return indentation


def line_strip(lines):
    """Remove leading and trailing empty lines from a line list
    
    Example:
        >>> line_strip([
        ...     ''
        ...     'a'
        ...     ''
        ... ])
        ['a']
    """
    lines = list(lines)
    kill = []
    for itt in range(0, len(lines)):
        if lines[itt]:
            break
        kill.append(itt)
    for itt in reversed(range(0, len(lines))):
        if lines[itt]:
            break
        kill.append(itt)
    for itt in reversed(sorted(kill)):
        del lines[itt]
    return lines


def format_literals(text, references_to_match=None, ref_template='%s'):
    """Replace single back-quotes with double ones.
    
    Optionally replace certain strings with references to other sections in
    this document.

    Args:
        text (str): The text to format literals in.
        references_to_match (list): List of strings which will be replaced
            by rst document references using the ref_template.
        ref_template (str): Template string for the document reference.

    Returns: str

    """
    if not references_to_match:
        references_to_match = []
    ref_template = ':ref:`{0}`'.format(ref_template)

    for match in reversed([x for x in LITERAL_REGEX.finditer(text)]):
        repl = ''
        start, end = match.span()

        if start > 0:
            pre_char = text[start - 1]
        else:
            pre_char = '\n'
        if pre_char != ' ' and pre_char != '\n':
            repl += '\ '

        body = match.group()[1:-1]
        if body in references_to_match:
            repl = ref_template % body.replace(' ', '-')
        else:
            repl += '``%s``' % body

        if end < len(text) - 2:
            post_char = text[end]
        else:
            post_char = ''
        if post_char not in [' ', '\n']:
            repl += '\ '

        text = text[:start] + repl + text[end:]

    return text


def write_rst_heading(write, text, heading_level, label_section=False,
                      label_template='%s'):
    """Write a rst heading element.
    
    Args:
        write (function): A writer function which will be called with each line
            to be written.
        text (str): The title to write.
        heading_level (int): Zero is a top level heading, 4 is the lowest.
        label_section (bool): If true add a sphinx label for referencing this
            section with. The label is formatted using the label_template.
        label_template (str): A template for formatting the name assigned to
            the rst label.

    """
    text = text.strip()
    if label_section:
        write('.. _%s:' % (label_template % text.replace(' ', '-')))
        write('')
    write(text)
    write(RST_HEADING_CHARS[heading_level] * len(text))
    write('')


def write_rst_section(write, text, indent_level=0):
    """Write out text with indentation striped.
    
    Optionally apply rst indentation as required.
    
    Args:
        write (function): A writer function which will be called with each line
            to be written.
        text (str): The text to write out.
        indent_level (int): The desired indentation level for the output text.
    
    """
    lines = line_strip(text.split('\n'))
    indentation = get_indentation(lines)
    for line in lines:
        write('%s%s' % (RST_INDENT * indent_level, line[indentation:]))
    write('')


def write_rose_command_reference(write, command_name):
    """Generate help text for a rose command.
    
    Args:
        write (function): A writer function which will be called with each line
            to be written.
        command_name (str): The name of the rose command to be documented (i.e.
            rose / rosie.

    """
    # Obtain help text.
    cmd = [command_name, 'doc']
    stdout = Popen(cmd, stdout=PIPE).communicate()[0]

    # Extract commands / aliases.
    commands = dict((x, y) for x, y, _ in ROSE_COMMAND_REGEX.findall(stdout))

    # For each command.
    for num, (command, help_text) in enumerate(sorted(commands.items())):
        # Deal with aliases.
        if '->' in command:
            # Command is an alias -> write a see also label.
            command, alias = command.split('->')
            # Don't label alias sections, we shouldn't be referencing them!
            write_rst_heading(write, command, 2)
            write('Alias - see :ref:`%s-label`' % (
                alias.strip().replace(' ', '-')))
            write('')
            continue

        # Replace single back-quotes with double ones and insert links to other
        # commands as required.
        help_text = format_literals(help_text, commands, '%s-label')

        # Split the help-text into sections.
        sections = OrderedDict(
            (a.strip(), b) for a, b in
             ROSE_HELP_SECTION_REGEX.findall(help_text))

        # The NAME section is not used.
        del sections['NAME']

        # Write command name as a heading.
        write_rst_heading(write, command, 2, True, '%s-label')

        # Write synopsis as a bash formatted code block.
        write('.. code-block:: bash')
        write('')
        write_rst_section(write, sections['SYNOPSIS'], indent_level=1)
        del sections['SYNOPSIS']

        # Write description as rst.
        write_rst_section(write, sections['DESCRIPTION'])
        del sections['DESCRIPTION']

        # Write out remaining sections.
        for title, section in sections.items():
            # Remove indentation and strip any leading/trailing new lines.
            section_lines = section.split('\n')
            indentation = get_indentation(section_lines)
            section_lines = line_strip([line[indentation:] for line in
                                        section_lines])

            # Write title as a paragraph.
            title = title.strip().upper()
            write('**%s**' % title)  # **bold-text**
            write('')

            if title in ROSE_OPTION_SECTIONS:
                # Write an option-description section, the option is a literal
                # and the description is rst.
                section_text = '\n'.join(section_lines)

                # Permit one or more lines at the top of an option section to
                # be rendered as a paragraph.
                header_lines = []
                header_lines_present = False
                for line in section_lines:
                    # Detect these "header lines".
                    if line and not line.startswith(' '):
                        header_lines.append(line)
                    elif not line:
                        header_lines_present = True
                        break
                    else:
                        break
                if header_lines_present:
                    # Write out these lines if detected
                    for line in header_lines:
                        write(line)
                        section_lines.remove(line)
                    write('')
                    # Remove these lines from the section.
                    section_text = '\n'.join(section_lines)

                # Write out options as definition blocks.
                for option, description in INDENT_REGEX.findall(section_text):
                    # Write out the option as a literal.
                    write('``%s``' % option)
                    # Write out the option text as a definition block.
                    # Description starts with a new line.
                    write_rst_section(write, description, 1)

            elif title in ROSE_CODE_SECTIONS:
                # Write a rst code-block.
                write('.. code-block:: %s' % ROSE_CODE_SECTIONS[title])
                write('')
                write_rst_section(write, section, 1)

            else:
                # Unknown documentation section - write an rst block.
                for line in section_lines:
                    write(line)
                write('')

        # Write section divide.
        if num != len(commands) -1:
            write('')
            write('----')

        write('')


class AutoCLIDoc(Directive):
    """A custom ReStructured Text directive for auto-documenting CLIs.

    Directive Args:
        cli_help_format (str): The type of command line help to generate help
            for (only option "rose").
        command (str): The command to document.

    """
    option_spec = {}
    required_arguments = 2

    def run(self):
        # The rose command to document (i.e. rose / rosie)
        cli_help_format, command = self.arguments[0:2]

        if cli_help_format == 'rose':
            # Generate CLI documentation as a list of rst formatted text lines.
            lines = []
            write = lines.append
            write_rose_command_reference(write, command)

            # Parse these lines into a docutills node.
            node = nodes.section()
            node.document = self.state.document
            nested_parse_with_titles(self.state, ViewList(lines), node)

            # Return the children of this node (the generated nodes).
            return node.children
        else:
            raise Exception('Invalid/Unsupported CLI help format "%s"' %
                            cli_help_format)


def setup(app):
    """Sphinx setup function."""
    app.add_directive('auto-cli-doc', AutoCLIDoc)
    return {'version': sphinx.__display_version__, 'parallel_read_safe': True}


if __name__ == '__main__':
    # Testing / Development.

    writer = print

    write_rst_heading(writer, 'Command Reference', 0)

    write_rst_heading(writer, 'Rose Commands', 1)
    write_rose_command_reference(writer, 'rose')

    write_rst_heading(writer, 'Rosie Commands', 1)
    write_rose_command_reference(writer, 'rosie')
