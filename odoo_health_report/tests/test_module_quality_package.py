# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
######################################################################################

import os
import shutil
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestModuleQualityPackage(TransactionCase):
    """Test suite for evaluating the module quality package model."""

    @classmethod
    def setUpClass(cls):
        """Set up the module quality model reference."""
        super().setUpClass()
        cls.ModuleQuality = cls.env['module.quality.package']

    def setUp(self):
        """Set up a temporary module environment to test code analysis functions."""
        super().setUp()
        self.tmpdir = tempfile.mkdtemp()
        self.module_path = os.path.join(self.tmpdir, 'fake_quality_module')
        os.makedirs(os.path.join(self.module_path, 'models'))
        os.makedirs(os.path.join(self.module_path, 'static', 'src', 'js'))
        os.makedirs(os.path.join(self.module_path, 'views'))
        with open(os.path.join(self.module_path, 'models', 'demo.py'), 'w', encoding='utf-8') as file:
            file.write('line1\nline2\n')
        with open(os.path.join(self.module_path, '__init__.py'), 'w', encoding='utf-8') as file:
            file.write('ignored\n')
        with open(os.path.join(self.module_path, 'static', 'src', 'js', 'demo.js'), 'w', encoding='utf-8') as file:
            file.write('line1\nline2\nline3\n')
        with open(os.path.join(self.module_path, 'views', 'demo.xml'), 'w', encoding='utf-8') as file:
            file.write('<root>\n</root>\n')

    def tearDown(self):
        """Clean up the temporary module environment."""
        shutil.rmtree(self.tmpdir)
        super().tearDown()

    def test_get_installed_modules_excludes_current_module(self):
        """Test if installed modules fetcher excludes the health report module itself."""
        modules = self.ModuleQuality.get_installed_modules()
        self.assertNotIn('odoo_health_report', modules.mapped('name'))
        self.assertTrue(all(module.state == 'installed' for module in modules))

    def test_count_lines_of_code_groups_modules_by_author(self):
        """Test if code line counting function properly calculates and groups by author."""
        fake_module = SimpleNamespace(
            name='fake_quality_module',
            author='Cybrosys',
            display_name='Fake Quality Module',
        )
        with (
            patch.object(type(self.ModuleQuality), 'get_installed_modules', return_value=[fake_module]),
            patch(
                'odoo.addons.odoo_health_report.models.module_quality_package.get_module_path',
                return_value=self.module_path,
            ),
        ):
            result = self.ModuleQuality.count_lines_of_code_in_modules()
        self.assertEqual(result['total_lines'], {
            'py_lines': 2,
            'js_lines': 3,
            'xml_lines': 2,
        })
        self.assertEqual(result['result']['Cybrosys'][0]['technical_name'], 'fake_quality_module')

    def test_fields_and_apps_overview_returns_expected_sections(self):
        """Test if the fields and apps overview returns the correct structural sections."""
        result = self.ModuleQuality.fields_and_apps_overview()
        overview = result['critical_overview']
        self.assertIn('overall_percentage', overview)
        self.assertIn('total_fields', overview)
        self.assertIn('stored', overview)
        self.assertIn('non_stored', overview)
        self.assertGreater(overview['total_fields']['value'], 0)

    def test_get_module_and_icons_returns_module_display_data(self):
        """Test if module details and icons are properly fetched and mapped."""
        with (
            patch(
                'odoo.addons.odoo_health_report.models.module_quality_package.get_modules',
                return_value=['base'],
            ),
            patch(
                'odoo.addons.odoo_health_report.models.module_quality_package.modules.module.get_module_icon',
                return_value='/base/icon.png',
            ),
            patch(
                'odoo.addons.base.wizard.base_module_update.BaseModuleUpdate.update_module',
                return_value=True,
            ),
        ):
            result = self.ModuleQuality.get_module_and_icons()
        self.assertEqual(result['base'], [
            self.env.ref('base.module_base').display_name,
            '/base/icon.png',
        ])

    def test_violation_helpers_delegate_to_check_violations_module(self):
        """Test if violation wrappers correctly delegate to the underlying violation checker."""
        with (
            patch(
                'odoo.addons.odoo_health_report.models.module_quality_package.'
                'check_violations.violations_report',
                return_value={'module': 'Base'},
            ) as report_mock,
            patch(
                'odoo.addons.odoo_health_report.models.module_quality_package.'
                'check_violations.get_violations',
                return_value={'style_lint_check': []},
            ) as violations_mock,
        ):
            self.assertEqual(self.ModuleQuality.check_violations_report('base'), {'module': 'Base'})
            self.assertEqual(self.ModuleQuality.check_violations('base'), {'style_lint_check': []})
        report_mock.assert_called_once_with(self.ModuleQuality, 'base')
        violations_mock.assert_called_once_with('base')
