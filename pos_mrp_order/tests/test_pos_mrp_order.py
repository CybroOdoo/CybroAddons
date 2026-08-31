# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: AYANA KP (odoo@cybrosys.com)
#
#    you can modify it under the terms of the GNU AFFERO
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
##############################################################################
from odoo.tests.common import TransactionCase, tagged
from odoo.exceptions import ValidationError, UserError


@tagged('post_install', '-at_install')
class TestPosMrpOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Create a component product
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
            'type': 'consu',
        })

        # Create a finished product template
        cls.product_tmpl = cls.env['product.template'].create({
            'name': 'Test Finished Product Template',
            'type': 'consu',
        })

        # Get the product product corresponding to the template
        cls.product = cls.product_tmpl.product_variant_id

    def test_01_product_template_onchange_no_bom(self):
        """Test product template onchange raises ValidationError if no BoM is defined."""
        self.product_tmpl.to_make_mrp = True
        with self.assertRaises(ValidationError):
            self.product_tmpl.onchange_to_make_mrp()

    def test_02_product_product_onchange_no_bom(self):
        """Test product product onchange raises ValidationError if no BoM is defined."""
        self.product.to_make_mrp = True
        with self.assertRaises(ValidationError):
            self.product.onchange_to_make_mrp()

    def test_03_onchange_with_bom(self):
        """Test product template and product product onchange succeeds if BoM is defined."""
        # Create BoM for the product template
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 2.0,
            })]
        })

        # Clear cache/recompute bom_count
        self.product_tmpl.invalidate_recordset(['bom_count'])
        self.product.invalidate_recordset(['bom_count'])

        # Try template onchange
        self.product_tmpl.to_make_mrp = True
        self.product_tmpl.onchange_to_make_mrp()  # Should not raise ValidationError

        # Try product onchange
        self.product.to_make_mrp = True
        self.product.onchange_to_make_mrp()  # Should not raise ValidationError

    def test_04_create_mrp_from_pos_exceptions(self):
        """Test validation exceptions for create_mrp_from_pos."""
        mrp_prod_model = self.env['mrp.production']

        # Case 1: Empty product list
        with self.assertRaises(UserError) as err:
            mrp_prod_model.create_mrp_from_pos([])
        self.assertEqual(err.exception.args[0], "No products provided.")

        # Case 2: No valid products (qty is 0 or less)
        with self.assertRaises(UserError) as err:
            mrp_prod_model.create_mrp_from_pos([{'id': self.product.id, 'qty': 0}])
        self.assertEqual(err.exception.args[0], "No valid products found.")

    def test_05_create_mrp_from_pos_no_bom(self):
        """Test that calling create_mrp_from_pos with a product that has no BoM does not create an MRP order."""
        mrp_prod_model = self.env['mrp.production']
        initial_count = mrp_prod_model.search_count([])

        product_list = [{
            'id': self.product.id,
            'qty': 1,
            'pos_reference': 'ORDER-0001',
        }]

        # Since the product has no BoM, it should skip it without raising errors or creating orders
        mrp_prod_model.create_mrp_from_pos(product_list)
        new_count = mrp_prod_model.search_count([])
        self.assertEqual(initial_count, new_count, "No MRP production order should be created for a product without BoM.")

    def test_06_create_mrp_from_pos_success(self):
        """Test successful creation of MRP order from POS order lines."""
        # Create BoM
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_tmpl.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 3.0,
            })]
        })

        product_list = [{
            'id': self.product.id,
            'qty': 2.0,
            'pos_reference': 'ORDER-0002',
        }]

        # Call create_mrp_from_pos
        self.env['mrp.production'].create_mrp_from_pos(product_list)

        # Retrieve the created MRP order
        mrp_order = self.env['mrp.production'].search([('origin', '=', 'POS-ORDER-0002')], limit=1)
        self.assertTrue(mrp_order, "MRP order should be successfully created.")
        self.assertEqual(mrp_order.product_id, self.product)
        self.assertEqual(mrp_order.product_qty, 2.0)
        self.assertEqual(mrp_order.state, 'confirmed', "Created MRP order should be in confirmed state.")

        # Check raw materials (move_raw_ids)
        # Expected raw material quantity = BoM line qty (3.0) * product_qty (2.0) = 6.0
        self.assertEqual(len(mrp_order.move_raw_ids), 1, "There should be exactly 1 raw material move.")
        raw_move = mrp_order.move_raw_ids[0]
        self.assertEqual(raw_move.product_id, self.component)
        self.assertEqual(raw_move.product_uom_qty, 6.0)
