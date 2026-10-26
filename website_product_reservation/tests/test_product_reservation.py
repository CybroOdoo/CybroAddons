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
#############################################################################
from odoo.tests import common, tagged


@tagged('post_install', '-at_install')
class TestProductReservation(common.TransactionCase):
    """Test suite for website_product_reservation models and business logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Reservation Customer',
            'email': 'customer@testreservation.com',
        })

        # Warehouse and default locations
        cls.warehouse = cls.env['stock.warehouse'].search(
            [('company_id', '=', cls.company.id)], limit=1
        )
        cls.source_location = cls.warehouse.lot_stock_id

        # Destination location for reservation
        cls.destination_location = cls.env['stock.location'].create({
            'name': 'Test Reservation Destination',
            'usage': 'internal',
            'location_id': cls.source_location.location_id.id,
            'company_id': cls.company.id,
        })
        cls.company.destination_location_id = cls.destination_location.id

        # Reservable product
        cls.product_template_reservable = cls.env['product.template'].create({
            'name': 'Reservable Desk',
            'type': 'consu',
            'is_storable': True,
            'reserve_products': True,
            'list_price': 150.0,
        })
        cls.product_reservable = cls.product_template_reservable.product_variant_id

        # Non-reservable product
        cls.product_template_standard = cls.env['product.template'].create({
            'name': 'Standard Chair',
            'type': 'consu',
            'is_storable': True,
            'reserve_products': False,
            'list_price': 50.0,
        })
        cls.product_standard = cls.product_template_standard.product_variant_id

        # Add initial stock on hand in source location
        cls.env['stock.quant']._update_available_quantity(
            cls.product_reservable,
            cls.source_location,
            50.0,
        )

    def test_01_product_template_reserve_products_field(self):
        """Test reserve_products boolean field on product template and variant."""
        self.assertTrue(
            self.product_template_reservable.reserve_products,
            "Product template should have reserve_products set to True"
        )
        self.assertTrue(
            self.product_reservable.reserve_products,
            "Product variant should inherit reserve_products from template"
        )
        self.assertFalse(
            self.product_template_standard.reserve_products,
            "Standard product template should have reserve_products set to False"
        )

        # Toggle field
        self.product_template_standard.reserve_products = True
        self.assertTrue(
            self.product_template_standard.reserve_products,
            "reserve_products field should be editable"
        )

    def test_02_res_config_settings_destination_location(self):
        """Test destination_location_id configuration via res.config.settings."""
        self.assertEqual(
            self.company.destination_location_id,
            self.destination_location,
            "Company destination location should match configured location"
        )

        new_dest_loc = self.env['stock.location'].create({
            'name': 'Alternative Reservation Destination',
            'usage': 'internal',
            'location_id': self.source_location.location_id.id,
            'company_id': self.company.id,
        })
        # Test related field on res.config.settings
        settings = self.env['res.config.settings'].new({
            'company_id': self.company.id,
            'destination_location_id': new_dest_loc.id,
        })
        self.assertEqual(
            settings.destination_location_id,
            new_dest_loc,
            "Settings should reflect assigned destination location"
        )
        self.company.destination_location_id = new_dest_loc
        self.assertEqual(
            self.company.destination_location_id,
            new_dest_loc,
            "Company destination location should be updated"
        )
        # Restore original for subsequent tests
        self.company.destination_location_id = self.destination_location

    def test_03_sale_order_reservation_state_and_flag(self):
        """Test sale.order custom 'reserve' state and is_reservation_order flag."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 2.0,
                'price_unit': 150.0,
            })],
        })

        self.assertTrue(
            sale_order.is_reservation_order,
            "Order should be marked as reservation order"
        )
        self.assertEqual(
            sale_order.state,
            'draft',
            "Initial order state should be draft"
        )

        # Set order state to 'reserve'
        sale_order.state = 'reserve'
        self.assertEqual(
            sale_order.state,
            'reserve',
            "State should successfully accept 'reserve'"
        )

    def test_04_create_and_cancel_reservation_stock(self):
        """Test create_reservation_stock and cancel_reservation_stock methods on sale.order.line."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 3.0,
                'price_unit': 150.0,
            })],
        })
        line = sale_order.order_line[0]

        # Call create_reservation_stock
        line.create_reservation_stock()
        self.assertTrue(
            line.picking_id,
            "Picking should be generated for the reserved order line"
        )
        picking = line.picking_id
        self.assertEqual(
            picking.partner_id,
            self.partner,
            "Picking partner should match order partner"
        )
        self.assertEqual(
            picking.location_id,
            self.source_location,
            "Source location should match warehouse lot_stock_id"
        )
        self.assertEqual(
            picking.location_dest_id,
            self.destination_location,
            "Destination location should match company destination_location_id"
        )
        self.assertEqual(
            picking.state,
            'done',
            "Picking should be validated to 'done' state"
        )

        # Cancel reservation stock (returns picking)
        line.cancel_reservation_stock(line.picking_id)
        # Check return picking was created and completed
        return_picking = self.env['stock.picking'].search([
            ('origin', 'ilike', picking.name)
        ], limit=1)
        self.assertTrue(
            return_picking,
            "A return picking should be created upon cancelling reservation stock"
        )
        self.assertEqual(
            return_picking.state,
            'done',
            "Return picking should be validated to 'done' state"
        )

    def test_05_create_reservation_stock_with_context(self):
        """Test create_reservation_stock with product_id and new_qty in context."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 150.0,
            })],
        })
        line = sale_order.order_line[0]

        # Use context override
        line.with_context(
            product_id=self.product_reservable,
            new_qty=4.0
        ).create_reservation_stock()

        self.assertTrue(line.picking_id, "Picking should be created")
        move = line.picking_id.move_ids[:1]
        self.assertEqual(
            move.product_uom_qty,
            4.0,
            "Move quantity should reflect context new_qty override"
        )

    def test_06_cancel_reservation_stock_late_availability(self):
        """Test cancel_reservation_stock when picking products_availability_state is late."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'price_unit': 150.0,
            })],
        })
        line = sale_order.order_line[0]
        # Create an unvalidated draft/assigned picking
        picking = self.env['stock.picking'].create({
            'partner_id': self.partner.id,
            'picking_type_id': self.env.ref('stock.picking_type_out').id,
            'location_id': self.source_location.id,
            'location_dest_id': self.destination_location.id,
            'move_ids': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 1.0,
                'quantity': 1.0,
                'uom_id': self.product_reservable.uom_id.id,
                'location_id': self.source_location.id,
                'location_dest_id': self.destination_location.id,
            })],
        })
        line.picking_id = picking.id
        picking.products_availability_state = 'late'

        line.cancel_reservation_stock(picking)
        self.assertEqual(
            picking.state,
            'cancel',
            "Late picking should be directly cancelled"
        )

    def test_07_action_make_draft_and_cancel_reservation(self):
        """Test sale.order action_make_draft and action_cancel_reservation."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 2.0,
                'price_unit': 150.0,
            })],
        })
        line = sale_order.order_line[0]
        line.create_reservation_stock()
        sale_order.state = 'reserve'

        # action_make_draft
        sale_order.action_make_draft()
        self.assertEqual(
            sale_order.state,
            'draft',
            "action_make_draft should switch state to draft"
        )

        # action_cancel_reservation
        sale_order.state = 'reserve'
        sale_order.action_cancel_reservation()
        self.assertEqual(
            sale_order.state,
            'cancel',
            "action_cancel_reservation should switch state to cancel"
        )

    def test_08_order_line_unlink_in_draft_reservation_order(self):
        """Test unlinking sale order line in a draft reservation order cancels reservation stock."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.partner.id,
            'is_reservation_order': True,
            'order_line': [(0, 0, {
                'product_id': self.product_reservable.id,
                'product_uom_qty': 2.0,
                'price_unit': 150.0,
            })],
        })
        line = sale_order.order_line[0]
        line.create_reservation_stock()
        picking = line.picking_id

        # Unlink the line while in draft reservation order
        line.unlink()
        self.assertFalse(
            sale_order.order_line,
            "Order line should be removed"
        )
        return_picking = self.env['stock.picking'].search([
            ('origin', 'ilike', picking.name)
        ], limit=1)
        self.assertTrue(
            return_picking,
            "Return picking should be triggered when unlinking line in draft reservation order"
        )
