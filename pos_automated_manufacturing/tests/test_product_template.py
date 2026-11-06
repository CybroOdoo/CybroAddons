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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import common
from odoo.exceptions import ValidationError


class TestProductTemplate(common.TransactionCase):
    """
    Test suite for validating product template constraints related to MRP.
    """
    def test_01_validation_error_no_bom(self):
        """Test that ValidationError is raised if to_create_mrp is True and no BoM exists."""
        product_no_bom = self.env['product.product'].create({
            'name': 'Product Without BoM',
            'type': 'consu',
        })

        with self.assertRaises(ValidationError):
            product_no_bom.product_tmpl_id.write({'to_create_mrp': True})

    def test_02_success_with_template_bom(self):
        """Test that enabling to_create_mrp succeeds when a template-level BoM exists."""
        product = self.env['product.product'].create({
            'name': 'Product With Template BoM',
            'type': 'consu',
        })
        component = self.env['product.product'].create({
            'name': 'Component Product',
            'type': 'consu',
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': component.id,
                'product_qty': 1.0,
            })],
        })

        # Should write successfully without raising ValidationError
        product.product_tmpl_id.write({'to_create_mrp': True, 'create_mrp_done': True})
        self.assertTrue(product.product_tmpl_id.to_create_mrp)
        self.assertTrue(product.product_tmpl_id.create_mrp_done)

    def test_03_success_with_variant_bom(self):
        """Test that enabling to_create_mrp succeeds when a variant-specific BoM exists."""
        product = self.env['product.product'].create({
            'name': 'Product With Variant BoM',
            'type': 'consu',
        })
        component = self.env['product.product'].create({
            'name': 'Component Product 2',
            'type': 'consu',
        })
        self.env['mrp.bom'].create({
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_id': product.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': component.id,
                'product_qty': 1.0,
            })],
        })

        product.product_tmpl_id.write({'to_create_mrp': True})
        self.assertTrue(product.product_tmpl_id.to_create_mrp)

    def test_04_disabled_flags_no_bom_required(self):
        """Test that to_create_mrp=False can be saved without requiring a BoM."""
        product = self.env['product.product'].create({
            'name': 'Product Flags False',
            'type': 'consu',
        })
        product.product_tmpl_id.write({'to_create_mrp': False, 'create_mrp_done': False})
        self.assertFalse(product.product_tmpl_id.to_create_mrp)

