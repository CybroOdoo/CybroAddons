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
from datetime import date, datetime

from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestWarrantyClaim(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.customer = cls.env['res.partner'].create({
            'name': 'Warranty Customer'})
        cls.product = cls.env['product.product'].create({
            'name': 'Claim Product',
            'is_warranty_available': True,
            'warranty_duration': 6,
        })
        cls.sale_order = cls.env['sale.order'].create({
            'partner_id': cls.customer.id,
            'order_line': [Command.create({'product_id': cls.product.id})],
        })
        cls.sale_order.date_order = datetime(2026, 1, 15, 10, 0)
        cls.claim = cls.env['warranty.claim'].create({
            'customer_id': cls.customer.id,
            'sale_order_id': cls.sale_order.id,
            'product_id': cls.product.id,
        })

    def test_claim_defaults_and_expiry_date(self):
        self.assertEqual(self.claim.state, 'draft')
        self.assertEqual(self.claim.user_id, self.env.user)
        self.assertEqual(self.claim.product_expiry_date, date(2026, 7, 15))

    def test_approve_and_reject(self):
        self.claim.change_status_approved()
        self.assertEqual(self.claim.state, 'approved')

        with self.assertRaises(UserError):
            self.claim.change_status_rejected()

        self.claim.action_reset_to_draft()
        self.claim.change_status_rejected()
        self.assertEqual(self.claim.state, 'rejected')
