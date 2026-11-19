# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jigin k(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestStockAnalysisByLocationReport(TransactionCase):

    def setUp(self):
        super().setUp()
        self.product_category = self.env['product.category'].create({
            'name': 'Test Category',
        })
        self.product_template = self.env['product.template'].create({
            'name': 'Test Product',
            'type': 'consu',
            'is_storable': True,
            'categ_id': self.product_category.id,
        })
        self.product_product = self.product_template.product_variant_ids[0]
        parent_location = self.env['stock.location'].search([
            ('usage', '=', 'view'),
            '|',
            ('company_id', '=', self.env.company.id),
            ('company_id', '=', False),
        ], limit=1)
        self.location = self.env['stock.location'].create({
            'name': 'Test Internal Location',
            'usage': 'internal',
            'company_id': self.env.company.id,
            'location_id': parent_location.id,
        })
        self.quant = self.env['stock.quant'].with_context(
            inventory_mode=True).create({
            'product_id': self.product_product.id,
            'location_id': self.location.id,
            'quantity': 10.0,
        })

    def test_product_template_qty_fields_exist(self):
        self.assertIn('qty_incoming', self.env['product.template']._fields)
        self.assertIn('qty_outgoing', self.env['product.template']._fields)
        self.assertIn('qty_avail', self.env['product.template']._fields)
        self.assertIn('qty_virtual', self.env['product.template']._fields)

    def test_product_product_qty_fields_exist(self):
        self.assertIn('qty_incoming', self.env['product.product']._fields)
        self.assertIn('qty_outgoing', self.env['product.product']._fields)
        self.assertIn('qty_avail', self.env['product.product']._fields)
        self.assertIn('qty_virtual', self.env['product.product']._fields)

    def test_product_template_compute_quantities(self):
        self.product_template._compute_quantities()
        self.assertGreaterEqual(self.product_template.qty_avail, 0)
        self.assertGreaterEqual(self.product_template.qty_incoming, 0)
        self.assertGreaterEqual(self.product_template.qty_outgoing, 0)
        self.assertIsNotNone(self.product_template.qty_virtual)

    def test_product_product_compute_quantities(self):
        self.product_product._compute_quantities_dict(
            lot_id=False, owner_id=False, package_id=False)
        self.assertGreaterEqual(self.product_product.qty_incoming, 0)
        self.assertGreaterEqual(self.product_product.qty_outgoing, 0)

    def test_stock_location_product_view_initialized(self):
        records = self.env['stock.location.product'].search([])
        self.assertIsNotNone(records)

    def test_stock_location_product_variant_view_initialized(self):
        records = self.env['stock.location.product.variant'].search([])
        self.assertIsNotNone(records)

    def test_stock_location_product_fields(self):
        model_fields = self.env['stock.location.product']._fields
        self.assertIn('product_id', model_fields)
        self.assertIn('location_id', model_fields)
        self.assertIn('on_hand_qty', model_fields)
        self.assertIn('qty_incoming', model_fields)
        self.assertIn('qty_outgoing', model_fields)
        self.assertIn('forecast_qty', model_fields)

    def test_stock_location_product_variant_fields(self):
        model_fields = self.env['stock.location.product.variant']._fields
        self.assertIn('product_id', model_fields)
        self.assertIn('location_id', model_fields)
        self.assertIn('on_hand_qty', model_fields)
        self.assertIn('qty_incoming', model_fields)
        self.assertIn('qty_outgoing', model_fields)
        self.assertIn('forecast_qty', model_fields)

    def test_wizard_creation_default_report_type(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product',
        })
        self.assertEqual(wizard.report_type, 'product')

    def test_wizard_report_type_product_variant(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product_variant',
            'product_variant_id': self.product_product.id,
        })
        self.assertEqual(wizard.report_type, 'product_variant')
        self.assertEqual(wizard.product_variant_id.id, self.product_product.id)

    def test_wizard_with_product_filter(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product',
            'product_id': self.product_template.id,
        })
        self.assertEqual(wizard.product_id.id, self.product_template.id)

    def test_query_data_product_all(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        result = report_model.query_data('product', False, False)
        self.assertIsInstance(result, list)

    def test_query_data_product_with_filter(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        result = report_model.query_data(
            'product', self.product_template.id, False)
        self.assertIsInstance(result, list)
        for row in result:
            self.assertIn('on_hand_qty', row)
            self.assertIn('qty_incoming', row)
            self.assertIn('qty_outgoing', row)
            self.assertIn('forecast_qty', row)

    def test_query_data_product_variant_all(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        result = report_model.query_data('product_variant', False, False)
        self.assertIsInstance(result, list)

    def test_query_data_product_variant_with_filter(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        result = report_model.query_data(
            'product_variant', False, self.product_product.id)
        self.assertIsInstance(result, list)

    def test_query_data_returns_correct_keys(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        result = report_model.query_data(
            'product', self.product_template.id, False)
        if result:
            row = result[0]
            self.assertIn('product', row)
            self.assertIn('location', row)
            self.assertIn('on_hand_qty', row)
            self.assertIn('forecast_qty', row)

    def test_get_report_values_product(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        data = {
            'report_type': 'product',
            'product_id': self.product_template.id,
            'product_variant_id': False,
        }
        result = report_model._get_report_values(None, data=data)
        self.assertIn('grouped_data', result)
        self.assertIn('var', result)
        self.assertIsInstance(result['grouped_data'], dict)

    def test_get_report_values_product_variant(self):
        report_model = self.env[
            'report.stock_analysis_by_location_report.report_stock_location']
        data = {
            'report_type': 'product_variant',
            'product_id': False,
            'product_variant_id': self.product_product.id,
        }
        result = report_model._get_report_values(None, data=data)
        self.assertIn('grouped_data', result)
        self.assertIn('var', result)

    def test_wizard_action_pdf_report(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product',
            'product_id': self.product_template.id,
        })
        action = wizard.action_pdf_report()
        self.assertIsInstance(action, dict)
        self.assertIn('type', action)

    def test_wizard_action_xlsx_report(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product',
            'product_id': self.product_template.id,
        })
        action = wizard.action_xlsx_report()
        self.assertIsInstance(action, dict)
        self.assertEqual(action.get('report_type'), 'xlsx')
        self.assertIn('data', action)

    def test_quant_creates_location_product_record(self):
        results = self.env['stock.location.product'].search([
            ('location_id', '=', self.location.id),
        ])
        product_ids = results.mapped('product_id').ids
        self.assertIn(self.product_template.id, product_ids)

    def test_quant_creates_location_product_variant_record(self):
        results = self.env['stock.location.product.variant'].search([
            ('location_id', '=', self.location.id),
        ])
        variant_ids = results.mapped('product_id').ids
        self.assertIn(self.product_product.id, variant_ids)

    def test_on_hand_qty_reflects_quant(self):
        results = self.env['stock.location.product'].search([
            ('location_id', '=', self.location.id),
            ('product_id', '=', self.product_template.id),
        ])
        self.assertTrue(results)
        self.assertGreater(results[0].on_hand_qty, 0)

    def test_wizard_no_product_filter(self):
        wizard = self.env['stock.location.report'].create({
            'report_type': 'product',
        })
        self.assertFalse(wizard.product_id)
        self.assertFalse(wizard.product_variant_id)
