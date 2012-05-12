"""Test the server recipe.

NB: zc.buildout.testing provides utilities for integration tests, with
an embedded http server, etc.
"""
import unittest

import os
import shutil
from tempfile import mkdtemp
from anybox.recipe.openerp import ServerRecipe
from anybox.recipe.openerp import vcs

def fakevcs_method(recipe, method_name):
    """Pure mockup to monkey-patch on recipe instances."""
    def meth(*args, **kwargs):
        return recipe._fake_vcs_log.append((method_name,) + args + (kwargs,))
    return meth

class TestServer(unittest.TestCase):

    def setUp(self):
        b_dir = self.buildout_dir = mkdtemp('test_oerp_recipe')
        self.buildout = {}
        self.buildout['buildout'] = {
            'directory': b_dir,
            'offline': False,
            'parts-directory': os.path.join(b_dir, 'parts'),
            'bin-directory': os.path.join(b_dir, 'bin'),
            }

    def tearDown(self):
        shutil.rmtree(self.buildout_dir)

    def make_recipe(self, name='openerp', **options):
        recipe = self.recipe = ServerRecipe(self.buildout, name, options)
        vcs.fakevcs_get_update = fakevcs_method(recipe, 'get_update')
        self.clear_vcs_log()

    def get_vcs_log(self):
        return self.recipe._fake_vcs_log

    def clear_vcs_log(self):
        self.recipe._fake_vcs_log = []

    def test_correct_v_6_1(self):
        self.make_recipe(version='6.1')
        self.assertEquals(self.recipe.version_wanted, '6.1-1')

    def test_retrieve_addons_local(self):
        """Setting up a local addons line."""
        addons_dir = os.path.join(self.buildout_dir, 'addons-custom')
        os.mkdir(addons_dir)
        self.make_recipe(version='6.1', addons='local addons-custom')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(self.get_vcs_log(), [])
        self.assertEquals(paths, [addons_dir])

    def test_retrieve_addons_local_options(self):
        """Addons options work for 'local' by testing (useless) subdir option.
        """
        custom_dir = os.path.join(self.buildout_dir, 'custom')
        addons_dir = os.path.join(custom_dir, 'addons')
        os.mkdir(custom_dir)
        os.mkdir(addons_dir)
        self.make_recipe(version='6.1', addons='local custom subdir=addons')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(self.get_vcs_log(), [])
        self.assertEquals(paths, [addons_dir])

    def test_retrieve_addons_vcs(self):
        """A VCS line in addons."""
        self.make_recipe(version='6.1', addons='fakevcs http://trunk.example '
                         'addons-trunk rev')
        # manual creation because fakevcs does nothing but retrieve_addons
        # has assertions on existence of target directories
        addons_dir = os.path.join(self.buildout_dir, 'addons-trunk')
        os.mkdir(addons_dir)
        paths = self.recipe.retrieve_addons()
        self.assertEquals(
            self.get_vcs_log(), [
                ('get_update', addons_dir, 'http://trunk.example', 'rev',
                 dict(offline=False)
                 )])
        self.assertEquals(paths, [addons_dir])

    def test_retrieve_addons_vcs_2(self):
        """Two VCS lines in addons."""
        self.make_recipe(version='6.1', addons=os.linesep.join((
                'fakevcs http://trunk.example addons-trunk rev',
                'fakevcs http://other.example addons-other 76')))
        # manual creation because fakevcs does nothing but retrieve_addons
        # has assertions on existence of target directories
        addons_dir = os.path.join(self.buildout_dir, 'addons-trunk')
        other_dir = os.path.join(self.buildout_dir, 'addons-other')
        os.mkdir(addons_dir)
        os.mkdir(other_dir)
        paths = self.recipe.retrieve_addons()
        self.assertEquals(
            self.get_vcs_log(), [
                ('get_update', addons_dir, 'http://trunk.example', 'rev',
                                 dict(offline=False)),
                ('get_update', other_dir, 'http://other.example', '76',
                                  dict(offline=False)),
                ])
        self.assertEquals(paths, [addons_dir, other_dir])

    def test_retrieve_addons_subdir(self):
        self.make_recipe(version='6.1', addons='fakevcs lp:openerp-web web '
                         'last:1 subdir=addons')
        # manual creation because fakevcs does nothing but retrieve_addons
        # has assertions on existence of target directories
        web_dir = os.path.join(self.buildout_dir, 'web')
        web_addons_dir = os.path.join(web_dir, 'addons')
        os.mkdir(web_dir)
        os.mkdir(web_addons_dir)
        paths = self.recipe.retrieve_addons()
        self.assertEquals(self.get_vcs_log(), [
                          ('get_update', web_dir, 'lp:openerp-web', 'last:1',
                           dict(offline=False))
                          ])
        self.assertEquals(paths, [web_addons_dir])

    def test_retrieve_addons_single(self):
        """The VCS is a whole addon."""
        self.make_recipe(version='6.1', addons='fakevcs custom addon last:1')
        # manual creation of our single addon
        addon_dir = os.path.join(self.buildout_dir, 'addon')
        os.mkdir(addon_dir)
        open(os.path.join(addon_dir, '__openerp__.py'), 'w').close()
        paths = self.recipe.retrieve_addons()
        self.assertEquals(paths, [addon_dir])
        self.assertEquals(os.listdir(addon_dir), ['addon'])
        self.assertEquals(os.listdir(os.path.join(addon_dir, 'addon')),
                                     ['__openerp__.py'])

    def test_retrieve_addons_single_collision(self):
        """The VCS is a whole addon, and there's a collision in renaming"""
        self.make_recipe(version='6.1', addons='fakevcs custom addon last:1')
        # manual creation of our single addon
        addon_dir = os.path.join(self.buildout_dir, 'addon')
        os.mkdir(addon_dir)
        os.mkdir(addon_dir + '_0')
        open(os.path.join(addon_dir, '__openerp__.py'), 'w').close()
        paths = self.recipe.retrieve_addons()
        self.assertEquals(paths, [addon_dir])
        self.assertEquals(os.listdir(addon_dir), ['addon'])
        self.assertEquals(os.listdir(os.path.join(addon_dir, 'addon')),
                                     ['__openerp__.py'])
