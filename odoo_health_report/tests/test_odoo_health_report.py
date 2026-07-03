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

from unittest.mock import patch
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOdooHealthReport(TransactionCase):
    """Test suite for the Odoo Health Report generation logic."""

    @classmethod
    def setUpClass(cls):
        """Set up report and module quality model references."""
        super().setUpClass()
        cls.Report = cls.env['report.odoo_health_report.odoo_health_report']
        cls.ModuleQuality = cls.env['module.quality.package']

    def test_get_report_values_returns_selected_module_quality_data(self):
        """Test if report values accurately extract quality data for the selected modules."""
        with (
            patch.object(
                type(self.ModuleQuality),
                'fields_and_apps_overview',
                return_value={'overview': True},
            ),
            patch.object(
                type(self.ModuleQuality),
                'count_lines_of_code_in_modules',
                return_value={'lines': True},
            ),
            patch.object(
                type(self.ModuleQuality),
                'check_violations_report',
                side_effect=lambda module: {'module': module},
            ) as report_mock,
        ):
            result = self.Report._get_report_values([], {
                'selected': ['module'],
                'module_selected': {'base': True, 'web': False},
            })
        self.assertEqual(result['doc_model'], 'module.quality.package')
        self.assertEqual(result['selected_module'], ['base'])
        self.assertEqual(result['module_quality']['field_details'], {'overview': True})
        self.assertEqual(result['module_quality']['count_lines'], {'lines': True})
        self.assertEqual(result['module_quality']['violations'], [{'module': 'base'}])
        report_mock.assert_called_once_with('base')

    def test_get_report_values_uses_all_installed_modules_when_none_selected(self):
        """Test if report values default to all installed modules when specific modules are not selected."""
        fake_modules = self.env['ir.module.module'].browse()
        with (
            patch.object(type(self.ModuleQuality), 'fields_and_apps_overview', return_value={}),
            patch.object(type(self.ModuleQuality), 'count_lines_of_code_in_modules', return_value={}),
            patch.object(type(self.ModuleQuality), 'get_installed_modules', return_value=fake_modules),
            patch.object(type(self.ModuleQuality), 'check_violations_report') as report_mock,
        ):
            result = self.Report._get_report_values([], {
                'context': {
                    'data': {
                        'selected': ['module'],
                        'module_selected': {},
                    },
                },
            })
        self.assertEqual(result['selected_module'], [])
        self.assertEqual(result['module_quality']['violations'], [])
        report_mock.assert_not_called()

    def test_get_report_values_returns_no_module_quality_when_module_not_selected(self):
        """Test if the report correctly returns no module quality data when none are applicable."""
        result = self.Report._get_report_values([1], {
            'selected': [],
            'module_selected': {},
        })
        self.assertIsNone(result['module_quality'])
        self.assertEqual(result['selected_module'], [])
        self.assertEqual(result['doc_ids'], [1])
