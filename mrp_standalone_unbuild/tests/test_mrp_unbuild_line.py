# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestMrpUnbuildLine(TransactionCase):
    """Tests for the MrpUnbuildLine model (models/mrp_unbuild_line.py)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.unit_uom = cls.env.ref('uom.product_uom_unit')
        cls.stock_quant = cls.env['stock.quant']

        cls.product = cls.env['product.product'].create({
            'name': 'Unbuild Line Test Product',
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.unit_uom.id,
            'uom_po_id': cls.unit_uom.id,
        })
        cls.component = cls.env['product.product'].create({
            'name': 'Unbuild Line Test Component',
            'type': 'consu',
            'is_storable': True,
            'uom_id': cls.unit_uom.id,
        })

        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_uom_id': cls.unit_uom.id,
            'product_qty': 1.0,
            'type': 'normal',
            'bom_line_ids': [
                (0, 0, {'product_id': cls.component.id, 'product_qty': 1.0}),
            ],
        })
        cls.unbuild = cls.env['mrp.unbuild'].create({
            'product_id': cls.product.id,
            'product_qty': 1.0,
            'product_uom_id': cls.unit_uom.id,
            'location_id': cls.stock_location.id,
            'location_dest_id': cls.stock_location.id,
        })

    def test_unbuild_line_creation(self):
        """Test that an mrp.unbuild.line record can be created with correct fields"""
        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': self.unbuild.id,
            'product_id': self.component.id,
            'qty': 5.0,
            'uom_id': self.unit_uom.id,
        })

        self.assertTrue(line.exists())
        self.assertEqual(line.unbuild_id, self.unbuild)
        self.assertEqual(line.product_id, self.component)
        self.assertEqual(line.qty, 5.0)
        self.assertEqual(line.uom_id, self.unit_uom)

    def test_compute_uom_id_from_product(self):
        """Test that _compute_uom_id sets uom_id to the product's default UOM"""
        kg_uom = self.env.ref('uom.product_uom_kgm')
        product_kg = self.env['product.product'].create({
            'name': 'Kg Product',
            'type': 'consu',
            'uom_id': kg_uom.id,
            'uom_po_id': kg_uom.id,
        })

        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': self.unbuild.id,
            'product_id': product_kg.id,
            'qty': 2.0,
        })

        self.assertEqual(line.uom_id, kg_uom)

    def test_compute_uom_id_clears_when_no_product(self):
        """Test that _compute_uom_id resets uom_id to False when product is cleared"""
        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': self.unbuild.id,
            'product_id': self.component.id,
            'qty': 1.0,
        })
        self.assertTrue(line.uom_id)

        line.product_id = False
        line._compute_uom_id()
        self.assertFalse(line.uom_id)

    def test_qty_on_hand_reflects_stock(self):
        """Test that qty_on_hand reflects the current on-hand stock of the line's product"""
        self.assertEqual(self.component.qty_available, 0.0)

        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': self.unbuild.id,
            'product_id': self.component.id,
            'qty': 1.0,
            'uom_id': self.unit_uom.id,
        })
        self.assertEqual(line.qty_on_hand, 0.0)

        self.stock_quant._update_available_quantity(
            self.component, self.stock_location, 10.0
        )
        self.env.flush_all()
        self.env.invalidate_all()
        self.assertEqual(line.qty_on_hand, 10.0)

    def test_unbuild_line_default_qty(self):
        """Test that default qty on mrp.unbuild.line is 1.0"""
        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': self.unbuild.id,
            'product_id': self.component.id,
            'uom_id': self.unit_uom.id,
        })
        self.assertEqual(line.qty, 1.0)

    def test_unbuild_line_cascade_delete_with_unbuild(self):
        """Test that mrp.unbuild.line is deleted (cascade) when its parent unbuild is deleted"""
        unbuild_to_delete = self.env['mrp.unbuild'].create({
            'product_id': self.product.id,
            'product_qty': 1.0,
            'product_uom_id': self.unit_uom.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.stock_location.id,
        })
        line = self.env['mrp.unbuild.line'].create({
            'unbuild_id': unbuild_to_delete.id,
            'product_id': self.component.id,
            'qty': 1.0,
            'uom_id': self.unit_uom.id,
        })
        line_id = line.id

        unbuild_to_delete.unlink()

        self.assertFalse(self.env['mrp.unbuild.line'].browse(line_id).exists())
