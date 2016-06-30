#!/usr/bin/env python
# Copyright 2016 ARC Centre of Excellence for Climate Systems Science
# author: Scott Wales <scott.wales@unimelb.edu.au>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from __future__ import print_function

ROSE_NS="namespace"
ROSE_UTIL="UTIL"
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
