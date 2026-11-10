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
from datetime import timedelta
from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import common, tagged
from odoo.addons.website_pre_booking.controllers.website_pre_booking import (
    WebsitePreBookingController,
)


@tagged('post_install', '-at_install')
class TestWebsitePreBooking(common.TransactionCase):
    """Test suite for website_pre_booking models and business logic."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Prebooking Customer',
            'email': 'customer@prebooktest.com',
        })
        cls.product = cls.env['product.template'].create({
            'name': 'Pre-bookable Widget',
            'list_price': 100.0,
            'pre_book': True,
            'pre_max_quantity': 10,
        })
        cls.website = cls.env['website'].search([], limit=1)

    def test_product_pre_booking_constraints(self):
        """Test date and quantity constraints on product.template."""
        today = fields.Date.context_today(self.env.user)
        with self.assertRaises(ValidationError):
            self.product.write({
                'from_date': today + timedelta(days=5),
                'to_date': today,
            })

        with self.assertRaises(ValidationError):
            self.product.write({'pre_max_quantity': -1})

    def test_is_pre_booking_available(self):
        """Test availability check based on dates, flag, and quantity."""
        today = fields.Date.context_today(self.env.user)
        self.product.write({
            'pre_book': True,
            'pre_max_quantity': 5,
            'from_date': today - timedelta(days=1),
            'to_date': today + timedelta(days=5),
        })
        self.assertTrue(self.product._is_pre_booking_available())

        # Expired to_date
        self.product.to_date = today - timedelta(days=1)
        self.assertFalse(self.product._is_pre_booking_available())

        # Future from_date
        self.product.write({
            'from_date': today + timedelta(days=2),
            'to_date': today + timedelta(days=10),
        })
        self.assertFalse(self.product._is_pre_booking_available())

        # Zero quantity
        self.product.write({
            'from_date': today - timedelta(days=1),
            'to_date': today + timedelta(days=5),
            'pre_max_quantity': 0,
        })
        self.assertFalse(self.product._is_pre_booking_available())

    def test_reserve_pre_booking_quantity(self):
        """Test reserving pre-booking quantities decreases available stock."""
        self.product.write({
            'pre_book': True,
            'pre_max_quantity': 8,
            'from_date': False,
            'to_date': False,
        })
        self.assertFalse(self.product._reserve_pre_booking_quantity(0))
        self.assertFalse(self.product._reserve_pre_booking_quantity(15))

        # Successful reservation of 3
        self.assertTrue(self.product._reserve_pre_booking_quantity(3))
        self.assertEqual(self.product.pre_max_quantity, 5)

    def test_pre_booking_creation_and_sequence(self):
        """Test creating a pre-booking generates sequence and validates."""
        booking = self.env['website.prebook'].create({
            'partner_id': self.partner.id,
            'product_id': self.product.id,
            'quantity': 2,
            'website_id': self.website.id,
        })
        self.assertTrue(booking.reference)
        self.assertNotEqual(booking.reference, 'New')
        self.assertEqual(booking.state, 'draft')

        with self.assertRaises(ValidationError):
            self.env['website.prebook'].create({
                'partner_id': self.partner.id,
                'product_id': self.product.id,
                'quantity': 0,
            })

    def test_action_confirm_creates_sale_order(self):
        """Test confirming a pre-booking creates a linked sale order."""
        booking = self.env['website.prebook'].create({
            'partner_id': self.partner.id,
            'product_id': self.product.id,
            'quantity': 2,
            'website_id': self.website.id,
        })
        self.assertFalse(booking.sale_id)
        booking.action_confirm()
        self.assertTrue(booking.sale_id)
        self.assertEqual(booking.sale_id.partner_id, self.partner)
        self.assertEqual(len(booking.sale_id.order_line), 1)
        self.assertEqual(booking.sale_id.order_line.product_uom_qty, 2)

        # Confirming again should be idempotent
        sale_order = booking.sale_id
        booking.action_confirm()
        self.assertEqual(booking.sale_id, sale_order)

    def test_controller_parse_quantity(self):
        """Test quantity parsing helper rejects non-positive or bad input."""
        self.assertEqual(WebsitePreBookingController._parse_quantity('5'), 5)
        self.assertEqual(WebsitePreBookingController._parse_quantity('0'), 0)
        self.assertEqual(WebsitePreBookingController._parse_quantity('-2'), 0)
        self.assertEqual(WebsitePreBookingController._parse_quantity('abc'), 0)
        self.assertEqual(WebsitePreBookingController._parse_quantity(None), 0)
