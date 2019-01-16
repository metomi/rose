#!/usr/bin/env python3

from rose.config_editor.pagewidget.table import PageTable, PageArrayTable, PageLatentTable
from rose.config_editor.ops.variable import VariableOperations
from rose.variable import Variable

from mock import patch

# Variables and metadata to try
variables = [
    Variable('string','foo',metadata={'id':'a','full_ns':'a'}),
    Variable('integer','1',metadata={'id':'b','full_ns':'b','length':':'})
    ]

def test_PageTable():
    # Mock out the helper classes for simplicity
    with patch('rose.config_editor.ops.variable.VariableOperations') as VarOps:
        with patch('rose.env') as Env:
            Env.contains_env_var.return_value = False
            var_ops = VarOps()
            table = PageTable(variables,[],var_ops,{})

def test_PageArrayTable():
    with patch('rose.config_editor.ops.variable.VariableOperations') as VarOps:
        with patch('rose.env') as Env:
            Env.contains_env_var.return_value = False
            var_ops = VarOps()
            table = PageArrayTable(variables,[],var_ops,{})

def test_PageLatentTable():
    with patch('rose.config_editor.ops.variable.VariableOperations') as VarOps:
        with patch('rose.env') as Env:
            Env.contains_env_var.return_value = False
            var_ops = VarOps()
            table = PageLatentTable(variables,[],var_ops,{'title': None})
