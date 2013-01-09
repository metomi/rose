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

from rosie.ws_client import RosieWSClient


class SearchManager():

    """Wrapper class for running searches."""

    def __init__(self, prefix):
        self.ws_client = RosieWSClient(prefix=prefix)

    def address_lookup(self, **items):
        """Return search results for a url lookup."""
        return self.ws_client.address_search(None, **items)

    def get_datasource(self):
        """Return the current datasource prefix."""
        return self.ws_client.prefix 

    def set_datasource(self, prefix):
        """Set the datasource."""
        self.ws_client = RosieWSClient(prefix=prefix)

    def ws_query(self, filters, **items):
        """Return search results for a query.""" 
        return self.ws_client.query(filters, **items)
    
    def ws_search(self, search, **items):
        """Return search results for a keyword search"""
        return self.ws_client.search(search, **items)
