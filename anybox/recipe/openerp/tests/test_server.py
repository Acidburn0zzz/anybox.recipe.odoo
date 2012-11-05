"""Test the server recipe.

NB: zc.buildout.testing provides utilities for integration tests, with
an embedded http server, etc.
"""
import unittest

import os
import sys
import shutil
from tempfile import mkdtemp
import anybox.recipe.openerp
from anybox.recipe.openerp.server import ServerRecipe
from anybox.recipe.openerp.testing import get_vcs_log, clear_vcs_log

class TestServer(unittest.TestCase):

    def setUp(self):
        b_dir = self.buildout_dir = mkdtemp('test_oerp_recipe')
        develop_dir = os.path.join(b_dir, 'develop-eggs')
        os.mkdir(develop_dir)
        clear_vcs_log()
        self.buildout = {}
        self.buildout['buildout'] = {
            'directory': b_dir,
            'offline': False,
            'parts-directory': os.path.join(b_dir, 'parts'),
            'bin-directory': os.path.join(b_dir, 'bin'),
            'find-links': '',
            'allow-hosts': '',
            'eggs-directory': 'eggs',
            'develop-eggs-directory': develop_dir,
            'python': 'main_python',
            }

        self.buildout['main_python'] = dict(executable=sys.executable)


    def tearDown(self):
        shutil.rmtree(self.buildout_dir)

    def make_recipe(self, name='openerp', **options):
        self.recipe = ServerRecipe(self.buildout, name, options)

    def test_retrieve_addons_local(self):
        """Setting up a local addons line."""
        addons_dir = os.path.join(self.buildout_dir, 'addons-custom')
        self.make_recipe(version='6.1', addons='local addons-custom')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(get_vcs_log(), [])
        self.assertEquals(paths, [addons_dir])

    def test_retrieve_addons_local_options(self):
        """Addons options work for 'local' by testing (useless) subdir option.
        """
        custom_dir = os.path.join(self.buildout_dir, 'custom')
        addons_dir = os.path.join(custom_dir, 'addons')
        self.make_recipe(version='6.1', addons='local custom subdir=addons')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(get_vcs_log(), [])
        self.assertEquals(paths, [addons_dir])

    def test_retrieve_addons_vcs(self):
        """A VCS line in addons."""
        self.make_recipe(version='6.1', addons='fakevcs http://trunk.example '
                         'addons-trunk rev')
        # manual creation because fakevcs does nothing but retrieve_addons
        # has assertions on existence of target directories
        addons_dir = os.path.join(self.buildout_dir, 'addons-trunk')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(
            get_vcs_log(), [
                (addons_dir, 'http://trunk.example', 'rev',
                 dict(offline=False, clear_locks=False)
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
        paths = self.recipe.retrieve_addons()
        self.assertEquals(
            get_vcs_log(), [
                (addons_dir, 'http://trunk.example', 'rev',
                 dict(offline=False, clear_locks=False)),
                (other_dir, 'http://other.example', '76',
                 dict(offline=False, clear_locks=False)),
                ])
        self.assertEquals(paths, [addons_dir, other_dir])

    def test_retrieve_addons_subdir(self):
        self.make_recipe(version='6.1', addons='fakevcs lp:openerp-web web '
                         'last:1 subdir=addons')
        # manual creation because fakevcs does nothing but retrieve_addons
        # has assertions on existence of target directories
        web_dir = os.path.join(self.buildout_dir, 'web')
        web_addons_dir = os.path.join(web_dir, 'addons')
        paths = self.recipe.retrieve_addons()
        self.assertEquals(get_vcs_log(), [
                          (web_dir, 'lp:openerp-web', 'last:1',
                           dict(offline=False, clear_locks=False))
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
        moved_addon = os.path.join(addon_dir, 'addon')
        self.assertTrue('__openerp__.py' in os.listdir(moved_addon))

        # update works
        self.recipe.retrieve_addons()
        self.assertEquals(get_vcs_log()[-1][0], moved_addon)


    def test_retrieve_addons_single_collision(self):
        """The VCS is a whole addon, and there's a collision in renaming"""
        self.make_recipe(version='6.1', addons='fakevcs custom addon last:1')
        addon_dir = os.path.join(self.buildout_dir, 'addon')
        os.mkdir(addon_dir)
        open(os.path.join(addon_dir, '__openerp__.py'), 'w').close()
        paths = self.recipe.retrieve_addons()
        self.assertEquals(paths, [addon_dir])
        self.assertEquals(os.listdir(addon_dir), ['addon'])
        self.assertTrue(
            '__openerp__.py' in os.listdir(os.path.join(addon_dir, 'addon')))

    def test_retrieve_addons_clear_locks(self):
        """Retrieving addons with vcs-clear-locks option."""
        addons_dir = os.path.join(self.buildout_dir, 'addons')
        options = dict(version='6.1', addons='fakevcs lp:my-addons addons -1')
        options['vcs-clear-locks'] = 'True'
        self.make_recipe(**options)
        self.recipe.retrieve_addons()
        self.assertEquals(get_vcs_log(), [
                          (addons_dir, 'lp:my-addons', '-1',
                           dict(offline=False, clear_locks=True))
                          ])

    def test_merge_requirements(self):
        self.make_recipe(version='6.1')
        self.recipe.version_detected = '6.1-1'
        self.recipe.merge_requirements()
        self.assertEquals(set(self.recipe.requirements),
                          set(['pychart', 'anybox.recipe.openerp',
                               'Pillow', 'openerp']))

    def test_merge_requirements_gunicorn(self):
        self.make_recipe(version='6.1', gunicorn='direct')
        self.recipe.version_detected = '6.1-1'
        self.recipe.merge_requirements()
        req = self.recipe.requirements
        self.assertTrue('gunicorn' in req)
        self.assertTrue('psutil' in req)

    def test_merge_requirements_devtools(self):
        self.make_recipe(version='6.1', with_devtools='true')
        self.recipe.version_detected = '6.1-1'
        self.recipe.merge_requirements()
        from anybox.recipe.openerp import devtools
        self.assertTrue(set(devtools.requirements).issubset(
                self.recipe.requirements))

    def test_merge_requirements_oe(self):
        self.make_recipe(version='nightly trunk 20121101',
                         openerp_command_name='oe')
        self.recipe.version_detected = '7.0alpha'
        self.recipe.merge_requirements()
        self.assertTrue('openerp-command' in self.recipe.requirements)

    def test_install_scripts_61(self):
        """A complete integration test again a typical OpenERP 6.1 setup.py

        Uses a minimal set of dependencies, though
        Actually tests nothing but that production of the scripts is possible.
        """
        test_dir = os.path.split(__file__)[0]
        oerp61_dir = os.path.join(test_dir, 'oerp61')
        self.make_recipe(version='local %s' % oerp61_dir,
                         gunicorn='direct',
                         with_devtools='true')
        self.recipe.version_detected = "6.1-20121003-233130"

        self.recipe.install_recipe_requirements()

        # minimal way of providing a gunicorn egg with the console
        # script entry point and requiring it for script creation
        self.recipe.develop(os.path.join(test_dir, 'fake_gunicorn'))
        self.recipe.options['eggs'] = 'gunicorn'

        self.recipe.install_requirements()
        self.recipe.develop(self.recipe.openerp_dir)

        bindir = os.path.join(self.buildout_dir, 'bin')
        os.mkdir(bindir)

        self.recipe._install_startup_scripts()
        binlist = os.listdir(bindir)

        for script in ('start_openerp', 'test_openerp',
                       'gunicorn_openerp', # missing at this point
                       'cron_worker_openerp',):
            if not script in binlist:
                self.fail("Script %r missing in bin directory." % script)
