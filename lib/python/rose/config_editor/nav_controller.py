

class NamespaceTreeManager(object):

    """This controls the navigation namespace tree structure."""
    
    def __init__(self, data, util, data_helper, tree_trigger_update):
        self.data = data
        self.util = util
        self.data_helper = data_helper
        self.tree_trigger_update = tree_trigger_update
        self.namespace_tree = {}  # Stores the namespace hierarchy

    def reload_namespace_tree(self, only_this_namespace=None,
                              only_this_config_name=None):
        """Make the tree of namespaces and load to the tree panel."""
        # Clear the old namespace tree information (selectively if necessary).
        if (only_this_namespace is not None and
            only_this_config_name is None):
            config_name = self.util.split_full_ns(self.data,
                                                  only_this_namespace)[0]
            only_this_config_name = config_name
            clear_namespace = only_this_namespace.rsplit("/", 1)[0]
            self.clear_namespace_tree(clear_namespace)
        elif only_this_config_name is not None:
            self.clear_namespace_tree(only_this_config_name)
        else:
            self.clear_namespace_tree()
        view_missing = self.data.page_ns_show_modes[
                                 rose.config_editor.SHOW_MODE_LATENT]
        # Reload the information into the tree.
        if only_this_config_name is None:
            configs = self.data.config.keys()
            configs.sort(rose.config.sort_settings)
            configs.sort(lambda x, y: cmp(self.data.config[y].is_top_level,
                                          self.data.config[x].is_top_level))
        else:
            configs = [only_this_config_name]
        for config_name in configs:
            config_data = self.data.config[config_name]
            if only_this_namespace:
                top_spaces = only_this_namespace.lstrip('/').split('/')[:-1]
            else:
                top_spaces = config_name.lstrip('/').split('/')
            self.update_namespace_tree(top_spaces, self.namespace_tree,
                                       prev_spaces=[])
            self.data.load_metadata_for_namespaces(config_name)
            meta_config = config_data.meta
            # Load tree from sections (usually vast majority of tree nodes)
            self.data.load_node_namespaces(config_name)
            for section_data in config_data.sections.get_all(
                                            no_latent=not view_missing):
                if section_data.metadata["id"] not in config_data.sections.now:
                    print "LATENT", section_data.metadata["id"], section_data.metadata["full_ns"]
                ns = section_data.metadata["full_ns"]
                self.data.namespace_meta_lookup.setdefault(ns, {})
                self.data.namespace_meta_lookup[ns].setdefault(
                                    'title', ns.split('/')[-1])
                spaces = ns.lstrip('/').split('/')
                self.update_namespace_tree(spaces,
                                           self.namespace_tree,
                                           prev_spaces=[])
            # Now load tree from variables
            for var in config_data.vars.get_all(no_latent=not view_missing):
                ns = var.metadata['full_ns']
                self.data.namespace_meta_lookup.setdefault(ns, {})
                self.data.namespace_meta_lookup[ns].setdefault(
                                    'title', ns.split('/')[-1])
                spaces = ns.lstrip('/').split('/')
                self.update_namespace_tree(spaces,
                                           self.namespace_tree,
                                           prev_spaces=[])
        # Perform an update.
        self.tree_trigger_update(only_this_namespace=only_this_namespace)

    def clear_namespace_tree(self, namespace=None):
        """Clear the namespace tree, or a subtree from namespace."""
        if namespace is None:
            spaces = []
        else:
            spaces = namespace.lstrip('/').split('/')
        tree = self.namespace_tree
        for space in spaces:
            if space not in tree:
                break
            tree = tree[space][0]
        tree.clear()

    def update_namespace_tree(self, spaces, subtree, prev_spaces):
        """Recursively load the namespace tree for a single path (spaces).

        The tree is specified with subtree, and it requires an array of names
        to load (spaces).

        """
        if spaces:
            this_ns = "/" + "/".join(prev_spaces + [spaces[0]])
            change = ""
            meta = self.data.namespace_meta_lookup.get(this_ns, {})
            meta.setdefault('title', spaces[0])
            latent_status = not self.data_helper.is_ns_content(this_ns)
            ignored_status = self.data_helper.get_ns_ignored_status(this_ns)
            print "Set", this_ns, repr(latent_status), repr(ignored_status)
            statuses = {rose.config_editor.SHOW_MODE_LATENT: latent_status,
                        rose.config_editor.SHOW_MODE_IGNORED: ignored_status}
            subtree.setdefault(spaces[0], [{}, meta, statuses, change])
            prev_spaces += [spaces[0]]
            self.update_namespace_tree(spaces[1:], subtree[spaces[0]][0],
                                       prev_spaces)
