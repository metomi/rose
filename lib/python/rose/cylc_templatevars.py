"""Load custom variables for template processor."""

import ast


class SafeVisitor(ast.NodeVisitor):
    """Abstract syntax tree node visitor for whitelisted evaluations.

    Attribues:
        whitelisted_nodes (tuple):
            Collection of ast nodes that this visitor is permitted to visit.
        whitelisted_functions (tuple):
            Collection of function names that this visitor is permitted to
            call.

            Note that only functions provided to the "eval()" call are
            available to the visitor in the first place.

    Raises:
        ValueError:
            In the event that this visitor is asked to visit a non-whitelisted
            node or call a non-whitelisted function.

    """

    def visit(self, node):
        if not isinstance(node, self.whitelisted_nodes):
            # permit only whitelisted operations
            raise ValueError(type(node))

        if isinstance(node, ast.Call):
            func = getattr(node, 'func', None)
            if isinstance(func, ast.Name):
                if func.id not in self.whitelisted_functions:
                    raise ValueError(func.id)
            else:
                raise ValueError(node.func)

        ast.NodeVisitor.visit(self, node)

    whitelisted_nodes = tuple()
    whitelisted_functions = tuple()


def load_template_vars(template_vars=None, template_vars_file=None):
    """Load template variables from key=value strings."""
    res = {}
    if template_vars_file:
        for line in open(template_vars_file):
            line = line.strip().split("#", 1)[0]
            if not line:
                continue
            key, val = line.split("=", 1)
            res[key.strip()] = templatevar_eval(val.strip())
    if template_vars:
        for pair in template_vars:
            key, val = pair.split("=", 1)
            res[key.strip()] = templatevar_eval(val.strip())
    return res


def listrange(*args):
    """A list equivalent to the Python range() function.

    Equivalent to list(range(*args))

    Examples:
        >>> listrange(3)
        [0, 1, 2]
        >>> listrange(0, 5, 2)
        [0, 2, 4]

    """
    return list(range(*args))


class SimpleVisitor(SafeVisitor):
    """Abstract syntax tree node visitor for simple safe operations."""

    whitelisted_nodes = (
        # top-level expression node
        ast.Expression,
        # constants: python3.8+
        # contants: python3.7
        ast.Num,
        ast.Str,
        # collections
        ast.List,
        ast.Tuple,
        ast.Dict,
        # intermediate opps
        ast.Load,
        ast.Name,
        # function calls (note only allow whitelisted calls)
        ast.Call
    )

    whitelisted_functions = (
        'range',
        'listrange'
    )


def _templatevar_eval(expr, **variables):
    """Safely evaluates template variables from strings.

    Examples:
        # constants
        >>> _templatevar_eval('"str"')
        'str'
        >>> _templatevar_eval('True')
        True
        >>> _templatevar_eval('1')
        1
        >>> _templatevar_eval('1.1')
        1.1
        >>> _templatevar_eval('None')

        # lists
        >>> _templatevar_eval('[]')
        []
        >>> _templatevar_eval('["str", True, 1, 1.1, None]')
        ['str', True, 1, 1.1, None]

        # tuples
        <<< _templatevar_eval('()')  # TODO
        ()
        >>> _templatevar_eval('("str", True, 1, 1.1, None)')
        ('str', True, 1, 1.1, None)

        # dicts
        >>> _templatevar_eval('{}')
        {}
        >>> _templatevar_eval(
        ... '{"a": "str", "b": True, "c": 1, "d": 1.1, "e": None}') == (
        ... {"a": "str", "b": True, "c": 1, "d": 1.1, "e": None})
        True

        # range
        >>> _templatevar_eval('range(10)')
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

        # listrange
        >>> _templatevar_eval('listrange(3)')
        [0, 1, 2]

        # errors
        >>> _templatevar_eval('1 + 1')
        Traceback (most recent call last):
        ValueError: <class '_ast.BinOp'>
        >>> _templatevar_eval('[0] + [1]')
        Traceback (most recent call last):
        ValueError: <class '_ast.BinOp'>
        >>> _templatevar_eval('list()')
        Traceback (most recent call last):
        ValueError: list
        >>> _templatevar_eval('__import__("shutil")')
        Traceback (most recent call last):
        ValueError: __import__

    """
    node = ast.parse(expr.strip(), mode='eval')
    SimpleVisitor().visit(node)
    # acceptable use of eval due to restricted language features
    return eval(  # nosec
        compile(node, '<string>', 'eval'),
        {'__builtins__': __builtins__, 'listrange': listrange},
        variables
    )


def templatevar_eval(var):
    """Parse tempalate variables from strings.

    Note:
        Wraps _templatevar_eval to provide more helpful error.

    Examples:
        # valid template variables
        >>> templatevar_eval('42')
        42
        >>> templatevar_eval('"string"')
        'string'
        >>> templatevar_eval('listrange(0, 3)')
        [0, 1, 2]

        # invalid templte variables
        >>> templatevar_eval('string')
        Traceback (most recent call last):
        Exception: Invalid template variable: string
        (note string values must be quoted)
        >>> templatevar_eval('[')
        Traceback (most recent call last):
        Exception: Invalid template variable: [
        (values must be valid Python literals)
        >>> templatevar_eval('MYVAR | len')  # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        Exception: \
        Invalid template variable: MYVAR | len
        Cannot use Jinja2 expressions.
        >>> templatevar_eval('range(5) | list')  # doctest: +NORMALIZE_WHITESPACE
        Traceback (most recent call last):
        Exception: \
        Invalid template variable: range(5) | list
        Cannot use Jinja2 expressions.
        Use listrange(...) instead of range(...) | list

    """
    try:
        return _templatevar_eval(var)
    except (ValueError, NameError):
        if (
            'range' in var
            and any([
                part.strip().startswith('list')
                for part in var.split('|')
            ])
        ):
            raise Exception(
                'Suite template variable will not work with Rose2/Cylc8'
                '\nJinja2 expression detected in: %s'
                '\nUse listrange(...) instead of range(...) | list' % var
            )
        elif any([
            string in var
            for string in (
                '|len',
                '| len',
                '| list',
                ']+range',
                '] + range',
                ']+[',
                '] + [',
            )
        ]):
            raise Exception(
                'Suite template variable will not work with Rose2/Cylc8'
                '\nJinja2 expression detected in: %s' % var
            )
        else:
            raise Exception(
                'Suite template variable will not work with Rose2/Cylc8'
            )
    except SyntaxError:
        raise Exception(
            'Suite template variable will not work with Rose2/Cylc8'
        )
