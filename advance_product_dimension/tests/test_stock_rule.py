# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
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
################################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'advance_product_dimension')
class TestStockRule(TransactionCase):
    """
    Test suite for models/stock_rule.py (StockRule model).

    Covers:
        - _get_dimension_procurement_values
        - _get_procurements_to_merge_groupby
        - _get_custom_move_fields
        - _prepare_mo_vals
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def test_get_dimension_procurement_values(self):
        """_get_dimension_procurement_values should return a tuple of dimension data."""
        vals = {
            'length': 2.0,
            'width': 3.0,
            'height': 4.0,
            'dimension_qty': 24.0,
            'dimension_method': 'length_width_height',
        }
        res = self.env['stock.rule']._get_dimension_procurement_values(vals)
        self.assertEqual(res, (2.0, 3.0, 4.0, 24.0, 'length_width_height'))

    def test_get_custom_move_fields(self):
        """_get_custom_move_fields should include dimension fields."""
        fields = self.env['stock.rule']._get_custom_move_fields()
        self.assertIn('length', fields)
        self.assertIn('width', fields)
        self.assertIn('height', fields)
        self.assertIn('dimension_qty', fields)
        self.assertIn('dimension_method', fields)

    def test_prepare_mo_vals(self):
        """_prepare_mo_vals should copy dimension values to the MO."""
        vals = {
            'length': 2.0,
            'width': 3.0,
            'height': 4.0,
            'dimension_qty': 24.0,
            'dimension_method': 'length_width_height',
            'date_planned': '2026-06-04 10:00:00',
            'company_id': self.env.company.id,
            'warehouse_id': self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1),
        }
        product = self.env['product.product'].create({'name': 'Test', 'type': 'consu'})
        bom = self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
        })

        location = self.env.ref('stock.stock_location_stock')
        mo_vals = self.env['stock.rule']._prepare_mo_vals(
            product, 1.0, product.uom_id, location, "Test MO", "Origin", self.env.company, vals, bom
        )
        self.assertEqual(mo_vals.get('length'), 2.0)
        self.assertEqual(mo_vals.get('width'), 3.0)
        self.assertEqual(mo_vals.get('height'), 4.0)
        self.assertAlmostEqual(mo_vals.get('dimension_qty'), 24.0)
        self.assertEqual(mo_vals.get('dimension_method'), 'length_width_height')
