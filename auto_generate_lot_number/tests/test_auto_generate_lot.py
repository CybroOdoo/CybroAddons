# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com/>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com/>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install', 'auto_generate_lot')
class TestAutoGenerateLotNumber(TransactionCase):
    """Test suite for auto generating serial and lot numbers."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.supplier_location = cls.env.ref('stock.stock_location_suppliers')
        cls.stock_location = cls.env.ref('stock.stock_location_stock')
        cls.customer_location = cls.env.ref('stock.stock_location_customers')
        cls.picking_type_in = cls.env.ref('stock.picking_type_in')
        cls.picking_type_out = cls.env.ref('stock.picking_type_out')

        cls.partner_supplier = cls.env['res.partner'].create({
            'name': 'Test Supplier Partner',
        })
        cls.partner_customer = cls.env['res.partner'].create({
            'name': 'Test Customer Partner',
        })

        # Tracked by Lot
        cls.product_lot = cls.env['product.product'].create({
            'name': 'Tracked by Lot Product',
            'is_storable': True,
            'tracking': 'lot',
            'prefix': 'LOTPROD-',
            'digits': 4,
        })

        # Tracked by Serial
        cls.product_serial = cls.env['product.product'].create({
            'name': 'Tracked by Serial Product',
            'is_storable': True,
            'tracking': 'serial',
            'prefix': 'SNPROD-',
            'digits': 5,
        })

        # Untracked Product
        cls.product_untracked = cls.env['product.product'].create({
            'name': 'Untracked Product',
            'is_storable': True,
            'tracking': False,
        })

    def _set_config(self, auto_generate=True, serial_type='global', prefix='TEST-', digits=4):
        """Helper to set ir.config_parameter values."""
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_bool('auto_generate_lot_number.is_auto_generate', bool(auto_generate))
        ICP.set_str('auto_generate_lot_number.serial_number_type', serial_type)
        ICP.set_str('auto_generate_lot_number.prefix', prefix)
        ICP.set_int('auto_generate_lot_number.digits', digits)
        self.env.company.check_auto_generate = bool(auto_generate)

    def test_01_global_mode_lot_generation(self):
        """Test auto generation of lot number in Global mode on incoming receipt."""
        self._set_config(auto_generate=True, serial_type='global', prefix='GLOB-', digits=4)

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_lot.id,
            'product_uom_qty': 10,
            'uom_id': self.product_lot.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        picking.action_confirm()

        # Preparing move line vals should generate lot_name with prefix and padding
        vals = move._prepare_move_line_vals(quantity=10)
        self.assertTrue(vals.get('lot_name'), "Lot name should be automatically generated")
        self.assertTrue(vals['lot_name'].startswith('GLOB-'), f"Lot name {vals['lot_name']} must start with GLOB-")
        self.assertEqual(len(vals['lot_name']), len('GLOB-') + 4, "Lot name must respect digits padding")

    def test_02_global_mode_serial_generation(self):
        """Test auto generation of serial numbers for serial-tracked product."""
        self._set_config(auto_generate=True, serial_type='global', prefix='SN-', digits=5)

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_serial.id,
            'product_uom_qty': 3,
            'uom_id': self.product_serial.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        picking.action_confirm()

        vals1 = move._prepare_move_line_vals(quantity=1)
        vals2 = move._prepare_move_line_vals(quantity=1)
        self.assertTrue(vals1.get('lot_name'))
        self.assertTrue(vals2.get('lot_name'))
        self.assertNotEqual(vals1['lot_name'], vals2['lot_name'], "Consecutive serial numbers must be unique")

    def test_03_product_wise_lot_generation(self):
        """Test auto generation of lot number in Product Wise mode."""
        self._set_config(auto_generate=True, serial_type='product')

        tmpl = self.product_lot.product_tmpl_id
        tmpl.write({
            'prefix': 'PWLOT-',
            'digits': 3,
            'number_next': 0,
        })

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_lot.id,
            'product_uom_qty': 5,
            'uom_id': self.product_lot.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        picking.action_confirm()

        if move.move_line_ids:
            self.assertEqual(move.move_line_ids[0].lot_name, 'PWLOT-001')
            self.assertEqual(tmpl.number_next, 1)
            # Next move line prepared gets next sequence
            vals2 = move._prepare_move_line_vals(quantity=5)
            self.assertEqual(vals2.get('lot_name'), 'PWLOT-002')
            self.assertEqual(tmpl.number_next, 2)
        else:
            vals = move._prepare_move_line_vals(quantity=5)
            self.assertEqual(vals.get('lot_name'), 'PWLOT-001')
            self.assertEqual(tmpl.number_next, 1)
            vals2 = move._prepare_move_line_vals(quantity=5)
            self.assertEqual(vals2.get('lot_name'), 'PWLOT-002')
            self.assertEqual(tmpl.number_next, 2)

    def test_04_outgoing_move_does_not_generate_lot(self):
        """Ensure delivery orders (outgoing) do NOT auto-generate new lots."""
        self._set_config(auto_generate=True, serial_type='global', prefix='OUT-', digits=4)

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_customer.id,
            'picking_type_id': self.picking_type_out.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_lot.id,
            'product_uom_qty': 2,
            'uom_id': self.product_lot.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.stock_location.id,
            'location_dest_id': self.customer_location.id,
        })
        picking.action_confirm()

        vals = move._prepare_move_line_vals(quantity=2)
        self.assertFalse(vals.get('lot_name'), "Outgoing moves must NOT auto-generate lot names")

    def test_05_disabled_auto_generation(self):
        """Test that nothing is generated when auto generation is disabled."""
        self._set_config(auto_generate=False)

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_lot.id,
            'product_uom_qty': 5,
            'uom_id': self.product_lot.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        picking.action_confirm()

        vals = move._prepare_move_line_vals(quantity=5)
        self.assertFalse(vals.get('lot_name'), "Disabled setting should not generate lot_name")

    def test_06_untracked_product_ignored(self):
        """Test that untracked products do not generate lot numbers."""
        self._set_config(auto_generate=True, serial_type='global')

        picking = self.env['stock.picking'].create({
            'partner_id': self.partner_supplier.id,
            'picking_type_id': self.picking_type_in.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        move = self.env['stock.move'].create({
            'product_id': self.product_untracked.id,
            'product_uom_qty': 1,
            'uom_id': self.product_untracked.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.supplier_location.id,
            'location_dest_id': self.stock_location.id,
        })
        picking.action_confirm()

        vals = move._prepare_move_line_vals(quantity=1)
        self.assertFalse(vals.get('lot_name'), "Untracked product must not generate lot_name")

    def test_07_res_config_settings_wizard(self):
        """Test reading and writing settings via res.config.settings wizard."""
        settings = self.env['res.config.settings'].create({
            'is_auto_generate': True,
            'serial_number_type': 'product',
            'prefix': 'WIZ-',
            'digits': 5,
        })
        settings.set_values()

        values = settings.get_values()
        self.assertTrue(values.get('is_auto_generate'))
        self.assertEqual(
            self.env['ir.config_parameter'].sudo().get_str('auto_generate_lot_number.serial_number_type'),
            'product'
        )
