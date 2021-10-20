# Copyright (C) British Crown (Met Office) & Contributors.
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

from textwrap import dedent

from metomi.rose.resource import (
    ROSE_CONF_PATH,
    ROSE_SITE_CONF_PATH,
    ResourceLocator,
)
import pytest


@pytest.fixture(scope='module')
def sys_site_user_config(mod_monkeypatch, mod_tmp_path):
    """Creates system, site and user configurations.

    * Patches ResourceLocator to use the system and user configs.
    * Unsets ROSE_*CONF_PATH envvars to prevent them effecting tests.

    """
    # unset ROSE_CONF_PATH env vars
    mod_monkeypatch.delenv(ROSE_CONF_PATH, raising=False)
    mod_monkeypatch.delenv(ROSE_SITE_CONF_PATH, raising=False)

    # create system, site and user configurations
    syst = mod_tmp_path / 'syst'
    site = mod_tmp_path / 'site'
    user = mod_tmp_path / 'user'
    syst.mkdir()
    site.mkdir()
    user.mkdir()
    with open(syst / 'rose.conf', 'w+') as conf:
        conf.write(
            dedent(
                '''
        all=syst
        syst=syst
        '''
            )
        )
    with open(site / 'rose.conf', 'w+') as conf:
        conf.write(
            dedent(
                '''
        all=site
        site=site
        '''
            )
        )
    with open(user / 'rose.conf', 'w+') as conf:
        conf.write(
            dedent(
                '''
        all=user
        user=user
        '''
            )
        )

    # patch the ResourceLocator
    mod_monkeypatch.setattr(
        'metomi.rose.resource.ResourceLocator.SYST_CONF_PATH', syst
    )
    mod_monkeypatch.setattr(
        'metomi.rose.resource.ResourceLocator.USER_CONF_PATH', user
    )

    return tuple(map(str, (syst, site, user)))


@pytest.fixture
def resource_locator():
    """Return a ResourceLocator instance for testing.

    Wipes the cached instance after each use.
    """
    resource_locator = ResourceLocator()
    yield resource_locator
    # prevent this instance being reused
    del resource_locator
    ResourceLocator._DEFAULT_RESOURCE_LOCATOR = None


def test_default(sys_site_user_config, resource_locator):
    """It should pick up the system and user config by default."""
    conf = resource_locator.get_conf()
    # both the syst and user config should have been loaded
    assert conf.get(['syst']).value == 'syst'
    assert conf.get(['user']).value == 'user'
    # the syst config should have been loaded before the user config
    assert conf.get(['all']).value == 'user'
    assert set(conf.value) == {'syst', 'user', 'all'}


def test_skip_no_read(sys_site_user_config, resource_locator, monkeypatch):
    """It should skip config files it can't read."""
    # make it look like all files are not readable.
    monkeypatch.setattr('os.access', lambda x, y: False)
    conf = resource_locator.get_conf()
    assert conf.value == {}


def test_rose_conf_path_blank(
    sys_site_user_config, resource_locator, monkeypatch
):
    """Setting ROSE_CONF_PATH= should prevent any conf files being loaded."""
    monkeypatch.setenv(ROSE_CONF_PATH, '')
    conf = resource_locator.get_conf()
    assert conf.value == {}


def test_rose_conf_path(sys_site_user_config, resource_locator, monkeypatch):
    """If ROSE_CONF_PATH is defined no other files should be loaded."""
    # set ROSE_CONF_PATH to point at the system config
    syst, site, *_ = sys_site_user_config
    monkeypatch.setenv(ROSE_CONF_PATH, syst)
    # set the ROSE_SITE_CONF_PATH just to make sure it is ignored
    monkeypatch.setenv(ROSE_SITE_CONF_PATH, site)
    conf = resource_locator.get_conf()
    assert conf.get(['syst']).value == 'syst'
    assert set(conf.value) == {'syst', 'all'}


def test_rose_site_conf_path(
    sys_site_user_config, resource_locator, monkeypatch
):
    """If ROSE_SITE_CONF_PATH is defined it should be loaded."""
    # set ROSE_SITE_CONF_PATH to point at the system config
    _, site, *_ = sys_site_user_config
    monkeypatch.setenv(ROSE_SITE_CONF_PATH, site)
    conf = resource_locator.get_conf()
    assert conf.get(['site']).value == 'site'
    assert conf.get(['user']).value == 'user'
    assert conf.get(['all']).value == 'user'
    assert set(conf.value) == {'syst', 'site', 'user', 'all'}
