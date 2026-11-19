# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import io
import json
from unittest.mock import Mock, patch
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import Forbidden
from werkzeug.wrappers import Response
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged
from odoo.addons.low_sale_report.controllers.low_sale_report import XLSXReportController


class MockResponse(Response):
    """Mock HTTP response wrapping BytesIO stream for report controller tests."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.stream = io.BytesIO()


@tagged('post_install', '-at_install')
class TestLowSaleReport(TransactionCase):
    """Test suite for Low Sales Report module."""

    @classmethod
    def setUpClass(cls):
        """Set up master test data including products, categories, teams, and sales orders."""
        super().setUpClass()
        cls.category = cls.env['product.category'].create({
            'name': 'Test Low Sale Category',
        })
        cls.team = cls.env['crm.team'].create({
            'name': 'Test Low Sale Team',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Customer',
        })
        cls.product_template = cls.env['product.template'].create({
            'name': 'Test Low Sale Product',
            'categ_id': cls.category.id,
            'list_price': 100.0,
            'type': 'consu',
        })
        cls.product = cls.product_template.product_variant_id

        today = fields.Date.context_today(cls.product_template)
        cls.today = today
        cls.order = cls.env['sale.order'].create({
            'partner_id': cls.partner.id,
            'team_id': cls.team.id,
            'date_order': today,
            'order_line': [(0, 0, {
                'product_id': cls.product.id,
                'product_uom_qty': 2.0,
                'price_unit': 100.0,
            })],
        })
        cls.order.action_confirm()

    def test_default_get_config_parameters(self):
        """Test wizard prefilling from ir.config_parameter and period calculations."""
        config_params = self.env['ir.config_parameter'].sudo()
        config_params.set_str('low_sale_report.product_type', 'template')
        config_params.set_float('low_sale_report.absolute_qty', 10.5)
        config_params.set_str('low_sale_report.analysed_period', 'last_month')

        fields_list = [
            'product_type', 'absolute_qty',
            'analysed_period_start', 'analysed_period_end',
        ]
        res = self.env['low.sale.report'].default_get(fields_list)
        self.assertEqual(res.get('product_type'), 'template')
        self.assertEqual(res.get('absolute_qty'), 10.5)
        self.assertTrue(res.get('analysed_period_start'))

        for period, months in [('last_3', 3), ('last_6', 6), ('last_12', 12)]:
            config_params.set_str('low_sale_report.analysed_period', period)
            res_period = self.env['low.sale.report'].default_get(fields_list)
            expected_start = res_period['analysed_period_end'] - relativedelta(months=months)
            self.assertEqual(res_period['analysed_period_start'], expected_start)

    def test_date_constraints(self):
        """Test validation constraint on analysis period start and end dates."""
        today = fields.Date.context_today(self.env.user)
        yesterday = today - relativedelta(days=1)
        tomorrow = today + relativedelta(days=1)

        valid_wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 5.0,
            'analysed_period_start': yesterday,
            'analysed_period_end': tomorrow,
        })
        self.assertTrue(valid_wizard)

        with self.assertRaises(ValidationError):
            self.env['low.sale.report'].create({
                'product_type': 'variant',
                'absolute_qty': 5.0,
                'analysed_period_start': tomorrow,
                'analysed_period_end': yesterday,
            })

    def test_action_pivot_low_sale_report_variant(self):
        """Test generating pivot report for product variants."""
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 5.0,
            'category': self.category.id,
            'sale_team': self.team.id,
        })
        action = wizard.action_pivot_low_sale_report()
        self.assertEqual(action.get('name'), 'Low Sales Pivot View Report')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'low.sale.pivot.view.report')
        self.assertEqual(action.get('view_mode'), 'pivot')

        created_records = self.env['low.sale.pivot.view.report'].browse(action['domain'][0][2])
        self.assertTrue(created_records)
        self.assertIn(self.product.id, created_records.mapped('product_id').ids)

    def test_action_pivot_low_sale_report_template(self):
        """Test generating pivot report for product templates."""
        wizard = self.env['low.sale.report'].create({
            'product_type': 'template',
            'absolute_qty': 5.0,
            'category': self.category.id,
            'sale_team': self.team.id,
        })
        action = wizard.action_pivot_low_sale_report()
        self.assertEqual(action.get('name'), 'Low Sales Pivot View Report')
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'low.sale.pivot.view.report')

        created_records = self.env['low.sale.pivot.view.report'].browse(action['domain'][0][2])
        self.assertTrue(created_records)
        self.assertIn(self.product_template.id, created_records.mapped('product_tmpl_id').ids)

    def test_action_pivot_no_data_raises_validation_error(self):
        """Test that action_pivot_low_sale_report raises ValidationError when no data matches."""
        empty_category = self.env['product.category'].create({'name': 'Empty Test Category'})
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 5.0,
            'category': empty_category.id,
        })
        with self.assertRaises(ValidationError):
            wizard.action_pivot_low_sale_report()

    def test_action_excel_low_sale_report(self):
        """Test action_excel_low_sale_report returns a valid report action dictionary."""
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 10.0,
        })
        action = wizard.action_excel_low_sale_report()
        self.assertEqual(action.get('type'), 'ir.actions.report')
        self.assertEqual(action.get('report_type'), 'low_sale_xlsx_download')
        self.assertEqual(action.get('data', {}).get('report_name'), 'Low Sales Report')
        self.assertIn('options', action.get('data', {}))

    def test_get_low_sale_xlsx_report(self):
        """Test generating binary Excel report data."""
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 10.0,
            'category': self.category.id,
        })
        options = {
            'form': {
                'product_type': 'variant',
                'analysed_period_start': False,
                'analysed_period_end': False,
                'absolute_qty': 10.0,
                'category': [self.category.id, self.category.name],
                'sale_team': False,
            }
        }
        mock_response = Mock()
        mock_response.stream = io.BytesIO()
        wizard.get_low_sale_xlsx_report(options, mock_response)
        xlsx_bytes = mock_response.stream.getvalue()
        self.assertTrue(len(xlsx_bytes) > 0)
        self.assertTrue(xlsx_bytes.startswith(b'PK'))

    def test_get_low_sale_xlsx_report_no_data(self):
        """Test get_low_sale_xlsx_report raises ValidationError when no records match."""
        empty_category = self.env['product.category'].create({'name': 'Empty Test Category 2'})
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 5.0,
            'category': empty_category.id,
        })
        options = {
            'form': {
                'product_type': 'variant',
                'analysed_period_start': False,
                'analysed_period_end': False,
                'absolute_qty': 5.0,
                'category': [empty_category.id, empty_category.name],
                'sale_team': False,
            }
        }
        mock_response = Mock()
        mock_response.stream = io.BytesIO()
        with self.assertRaises(ValidationError):
            wizard.get_low_sale_xlsx_report(options, mock_response)

    def test_controller_xlsx_report(self):
        """Test XLSXReportController routes and downloads Excel report."""
        controller = XLSXReportController()
        wizard = self.env['low.sale.report'].create({
            'product_type': 'variant',
            'absolute_qty': 10.0,
        })
        self.assertTrue(wizard)
        options = {
            'form': {
                'product_type': 'variant',
                'analysed_period_start': False,
                'analysed_period_end': False,
                'absolute_qty': 10.0,
                'category': False,
                'sale_team': False,
            }
        }
        mock_req = Mock()
        mock_req.session.uid = self.env.uid
        mock_req.env = self.env

        def make_response(data, headers=None):
            return MockResponse(data, headers=headers or [])

        mock_req.make_response = make_response

        with patch('odoo.addons.low_sale_report.controllers.low_sale_report.request', mock_req):
            response = controller.get_report_xlsx(
                model='low.sale.report',
                options=json.dumps(options),
                output_format='xlsx',
                report_name='Low_Sale_Report',
            )
            cookie_header = response.headers.get('Set-Cookie', '')
            self.assertIn('fileToken=dummy-because-api-expects-one', cookie_header)
            self.assertTrue(len(response.stream.getvalue()) > 0)

    def test_controller_unauthorized_model_access(self):
        """Test that get_report_xlsx blocks arbitrary model execution."""
        controller = XLSXReportController()
        mock_req = Mock()
        mock_req.session.uid = self.env.uid
        mock_req.env = self.env
        with patch('odoo.addons.low_sale_report.controllers.low_sale_report.request', mock_req):
            with self.assertRaises(Forbidden):
                controller.get_report_xlsx(
                    model='res.users',
                    options='{}',
                    output_format='xlsx',
                    report_name='Low_Sales_Report',
                )

    def test_res_config_settings_storage(self):
        """Test setting and retrieving configuration settings."""
        settings = self.env['res.config.settings'].create({
            'product_type': 'template',
            'analysed_period': 'last_6',
            'absolute_qty': 15.0,
        })
        settings.execute()
        config = self.env['ir.config_parameter'].sudo()
        self.assertEqual(config.get_str('low_sale_report.product_type'), 'template')
        self.assertEqual(config.get_str('low_sale_report.analysed_period'), 'last_6')
        self.assertEqual(config.get_float('low_sale_report.absolute_qty'), 15.0)
