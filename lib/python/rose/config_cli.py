# -*- coding: utf-8 -*-
#-----------------------------------------------------------------------------
# (C) British Crown Copyright 2012 Met Office.
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
"""Implements the "rose config" command."""

from rose.config import ConfigDumper, ConfigLoader, ConfigNode
from rose.opt_parse import RoseOptionParser
from rose.resource import ResourceLocator
import rose.macro
import os
import sys


def get_meta_path(root_node, rel_path=None, meta_key=False):
    if meta_key:
        dir_path = None
    elif rel_path:
        dir_path = os.getcwd() + "/" + rel_path
    else:
        dir_path = os.getcwd()
        
    meta_dir = rose.macro.load_meta_path(config=root_node, directory=dir_path)[0]
    if meta_dir is not None:
        return meta_dir + "/rose-meta.conf"
    else:
        return None


def main():
    """Implement the "rose config" command."""
    opt_parser = RoseOptionParser()
    opt_parser.add_my_options("default", "files", "keys", "no_ignore", "meta", 
                              "meta_key")
    opts, args = opt_parser.parse_args()
    rose.macro.add_site_meta_paths()
    rose.macro.add_env_meta_paths()
    
    if opts.meta_key:
        opts.meta = True
    
    if opts.files and opts.meta_key:
        sys.stderr.write("Cannot specify both a file and meta key.")
        return None
        
    try:
        if opts.files:
            root_node = ConfigNode()
            for file in opts.files:
                if file == "-":
                    ConfigLoader()(sys.stdin, root_node)
                    sys.stdin.close()
                else:
                    if opts.meta:
                        rel_path = "/".join(file.split("/")[:-1])
                        fpath = get_meta_path(root_node, rel_path)
                        if fpath is not None:
                            ConfigLoader()(fpath, root_node)
                        else:
                            print "No metadata found for {0}".format(str(file))
                    else:
                        ConfigLoader()(file, root_node)
        else:
            if opts.meta:
                root_node = ConfigNode()
                if opts.meta_key:
                    root_node.set(["meta"], opts.meta_key)
                
                fpath = get_meta_path(root_node, meta_key=opts.meta_key)    
                if fpath is not None:
                    ConfigLoader()(fpath, root_node)
                else:
                    print "No metadata found."
            else:
                root_node = ResourceLocator.default().get_conf()
            
    except SyntaxError as e:
        sys.exit(repr(e))
    if opts.quietness:
        if root_node.get(args, opts.no_ignore) is None:
            sys.exit(1)
    elif opts.keys_mode:
        try:
            keys = root_node.get(args, opts.no_ignore).value.keys()
        except:
            sys.exit(1)
        keys.sort()
        for key in keys:
            print key
    elif len(args) == 0:
        ConfigDumper()(root_node)
    else:
        node = root_node.get(args, opts.no_ignore)
        if node is not None and isinstance(node.value, dict):
            keys = node.value.keys()
            keys.sort()
            for key in keys:
                node_of_key = node.get([key], opts.no_ignore)
                value = node_of_key.value
                state = node_of_key.state
                string = "%s%s=%s" % (state, key, value)
                lines = string.splitlines()
                print lines[0]
                i_equal = len(state + key) + 1
                for line in lines[1:]:
                    print " " * i_equal + line
        else:
            if node is None:
                if opts.default is None:
                    sys.exit(1)
                print opts.default
            else:
                print node.value


if __name__ == "__main__":
    main()
