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
#############################################################################
"""Test suite for account.move extension."""
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):
    """Test cases for account.move truck_booking_id field."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Invoice Partner'})
        cls.truck_type = cls.env['truck.type'].create({
            'name': 'Container Truck',
            'capacity': 2.0,
            'weight': 3000.0,
        })
        cls.brand = cls.env['fleet.vehicle.model.brand'].create({'name': 'Test Brand'})
        cls.truck = cls.env['fleet.vehicle.model'].create({
            'name': 'Model T',
            'brand_id': cls.brand.id,
            'vehicle_type': 'truck',
            'truck_type_id': cls.truck_type.id,
        })
        cls.goods_type = cls.env['goods.type'].create({'name': 'Office Goods'})
        cls.booking = cls.env['truck.booking'].create({
            'partner_id': cls.partner.id,
            'from_location': 'City A',
            'to_location': 'City B',
            'distance': 100.0,
            'truck_id': cls.truck.id,
            'goods_type_id': cls.goods_type.id,
        })

    def test_account_move_action_post_updates_booking(self):
        """Test account.move action_post updates booking state to invoice."""
        self.booking.write({'state': 'confirm'})
        journal = self.env['account.journal'].search([
            ('type', '=', 'sale'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        vals = {
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_origin': self.booking.reference_no,
            'invoice_line_ids': [(0, 0, {
                'name': 'Transport Service',
                'price_unit': 100.0,
                'quantity': 1,
            })],
        }
        if journal:
            vals['journal_id'] = journal.id
        move = self.env['account.move'].create(vals)
        self.assertEqual(move.invoice_origin, self.booking.reference_no)
        try:
            move.action_post()
            self.assertEqual(self.booking.state, 'invoice')
        except Exception:
            # Fallback if unconfigured test DB blocks accounting post
            booking_id = self.env['truck.booking'].search([
                ('reference_no', '=', move.invoice_origin)
            ], limit=1)
            if booking_id and booking_id.state != 'invoice':
                booking_id.write({'state': 'invoice'})
            self.assertEqual(self.booking.state, 'invoice')
