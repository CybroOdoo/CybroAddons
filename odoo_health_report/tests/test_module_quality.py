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
import xml.etree.ElementTree as ET
from unittest.mock import patch

from odoo.exceptions import AccessError
from odoo.modules import get_module_path
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.odoo_health_report.models import module_quality_package


@tagged('post_install', '-at_install')
class TestModuleQuality(TransactionCase):
    """Tests for the module quality model and the report values."""

    def setUp(self):
        super().setUp()
        self.quality = self.env['module.quality.package']

    def test_installed_modules_exclude_self(self):
        modules = self.quality.get_installed_modules()
        self.assertTrue(modules)
        self.assertNotIn('odoo_health_report', modules.mapped('name'))
        self.assertTrue(all(state == 'installed' for state in modules.mapped('state')))

    def test_count_lines_of_code(self):
        data = self.quality.count_lines_of_code_in_modules()
        self.assertIn('result', data)
        self.assertIn('total_lines', data)
        self.assertGreater(data['total_lines'].get('py_lines', 0), 0)
        for entries in data['result'].values():
            for entry in entries:
                self.assertIn('technical_name', entry)
                self.assertIn('py_lines', entry)

    def test_count_lines_skips_modules_without_path(self):
        with patch.object(module_quality_package, 'get_module_path', return_value=False):
            data = self.quality.count_lines_of_code_in_modules()
        self.assertEqual(data['result'], {})
        self.assertEqual(data['total_lines'], {})

    def test_fields_and_apps_overview(self):
        overview = self.quality.fields_and_apps_overview()['critical_overview']
        total = overview['total_fields']['value']
        stored = overview['stored']['value']
        non_stored = overview['non_stored']['value']
        self.assertGreater(total, 0)
        self.assertEqual(total, stored + non_stored)
        self.assertTrue(0 <= overview['overall_percentage']['value'] <= 100)

    def test_get_module_and_icons(self):
        modules = self.quality.get_module_and_icons()
        self.assertIn('base', modules)
        self.assertNotIn('odoo_health_report', modules)
        self.assertEqual(len(modules['base']), 2)

    def test_check_violations_methods(self):
        fake = {
            'style_lint_check': [], 'code_quality_check': [], 'mi_check': [],
            'import_sort_check': [], 'code_format_check': [], 'cc_check': {},
            'security_scan': [], 'odoo_standards_check': [],
        }
        with patch.object(module_quality_package.check_violations, 'get_violations',
                          return_value=fake):
            self.assertEqual(self.quality.check_violations('base'), fake)
            report = self.quality.check_violations_report('base')
        self.assertEqual(report['module'], self.env.ref('base.module_base').display_name)
        self.assertEqual(set(report['violations']), {
            'odoo_standards', 'style_lint', 'code_quality', 'maintainability_index',
            'import_sort', 'code_format', 'code_complexity', 'security_scan'})

    def test_report_values_selected_module(self):
        fake = {'module': 'Base', 'violations': {}}
        report = self.env['report.odoo_health_report.odoo_health_report']
        data = {'selected': ['module'], 'module_selected': {'base': True, 'web': False}}
        with patch.object(type(self.quality), 'check_violations_report', return_value=fake):
            values = report._get_report_values([], data=data)
        self.assertEqual(values['selected_module'], ['base'])
        self.assertEqual(len(values['module_quality']['violations']), 1)
        self.assertIn('field_details', values['module_quality'])
        self.assertIn('count_lines', values['module_quality'])

    def test_report_values_all_modules(self):
        fake = {'module': 'Any', 'violations': {}}
        report = self.env['report.odoo_health_report.odoo_health_report']
        data = {'context': {'data': {'selected': ['module'], 'module_selected': {}}}}
        installed = self.quality.get_installed_modules()
        with patch.object(type(self.quality), 'check_violations_report', return_value=fake):
            values = report._get_report_values([], data=data)
        self.assertEqual(len(values['module_quality']['violations']), len(installed))

    def test_report_values_nothing_selected(self):
        report = self.env['report.odoo_health_report.odoo_health_report']
        values = report._get_report_values([], data={'selected': ['other']})
        self.assertIsNone(values['module_quality'])
        self.assertEqual(values['doc_model'], 'module.quality.package')

    def test_report_action_and_menu_exist(self):
        action = self.env.ref('odoo_health_report.action_odoo_health_report')
        self.assertEqual(action.model, 'module.quality.package')
        self.assertTrue(self.env.ref('odoo_health_report.action_dashboard_wrapper'))
        self.assertTrue(self.env.ref('odoo_health_report.odoo_health_report_menu_health_dashboard'))

    def test_pdf_report_template_line_count_alignment(self):
        """Verify the report XML aligns JavaScript Lines with js_lines and Python Lines with py_lines."""
        report_xml = os.path.join(get_module_path('odoo_health_report'), 'reports', 'odoo_health_report.xml')
        tree = ET.parse(report_xml)
        root = tree.getroot()
        headers = [' '.join(th.text.split()) for th in root.iter('th') if th.text and 'Lines' in th.text]
        self.assertIn('JavaScript Lines', headers)
        self.assertIn('Python Lines', headers)
        self.assertIn('XML Lines', headers)
        js_idx = headers.index('JavaScript Lines')
        py_idx = headers.index('Python Lines')

        data_cells = [td.attrib.get('t-out', '') for td in root.iter() if td.attrib.get('t-out', '').endswith("_lines']")]
        self.assertEqual(len(data_cells), 3)
        self.assertEqual(data_cells[js_idx], "author_module['js_lines']")
        self.assertEqual(data_cells[py_idx], "author_module['py_lines']")

    def test_rpc_group_check(self):
        """Non-system users cannot call quality metrics methods."""
        user = self.env['res.users'].create({
            'name': 'Test Regular User',
            'login': 'test_regular_user',
        })
        with self.assertRaises(AccessError):
            self.quality.with_user(user).count_lines_of_code_in_modules()
        with self.assertRaises(AccessError):
            self.quality.with_user(user).fields_and_apps_overview()
        with self.assertRaises(AccessError):
            self.quality.with_user(user).get_module_and_icons()
        with self.assertRaises(AccessError):
            self.quality.with_user(user).check_violations('base')
