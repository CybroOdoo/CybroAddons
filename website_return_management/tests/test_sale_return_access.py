# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestSaleReturnAccess(TransactionCase):
    """Cover the ir.access rows added for sale.return: an internal user
    keeps full access, a portal user is scoped to their own partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({'name': 'Return Test Product'})
        cls.partner_a = cls.env['res.partner'].create({'name': 'Return Customer A'})
        cls.partner_b = cls.env['res.partner'].create({'name': 'Return Customer B'})
        cls.portal_user_a = new_test_user(
            cls.env, login='return_portal_a', groups='base.group_portal',
            partner_id=cls.partner_a.id)
        cls.portal_user_b = new_test_user(
            cls.env, login='return_portal_b', groups='base.group_portal',
            partner_id=cls.partner_b.id)
        cls.sale_order_a = cls.env['sale.order'].create({'partner_id': cls.partner_a.id})
        cls.return_a = cls.env['sale.return'].create({
            'product_id': cls.product.id,
            'sale_order_id': cls.sale_order_a.id,
            'partner_id': cls.partner_a.id,
            'quantity': 1,
        })

    def test_owner_can_read_own_return(self):
        self.return_a.with_user(self.portal_user_a).read(['name'])

    def test_other_portal_user_cannot_read_return(self):
        with self.assertRaises(AccessError):
            self.return_a.with_user(self.portal_user_b).read(['name'])

    def test_portal_user_can_create_own_return(self):
        so = self.env['sale.order'].create({'partner_id': self.partner_a.id})
        sale_return = self.env['sale.return'].with_user(self.portal_user_a).create({
            'product_id': self.product.id,
            'sale_order_id': so.id,
            'partner_id': self.partner_a.id,
            'quantity': 1,
        })
        self.assertTrue(sale_return)

    def test_portal_user_cannot_create_return_for_other_partner(self):
        so = self.env['sale.order'].create({'partner_id': self.partner_b.id})
        with self.assertRaises(AccessError):
            self.env['sale.return'].with_user(self.portal_user_a).create({
                'product_id': self.product.id,
                'sale_order_id': so.id,
                'partner_id': self.partner_b.id,
                'quantity': 1,
            })

    def test_portal_user_cannot_unlink_own_return(self):
        """cr only - the portal grant deliberately excludes write/unlink."""
        with self.assertRaises(AccessError):
            self.return_a.with_user(self.portal_user_a).unlink()
