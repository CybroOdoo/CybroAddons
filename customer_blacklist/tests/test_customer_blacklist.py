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
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestCustomerBlacklist(TransactionCase):
    """Test suite for customer blacklist functionality across partners,

    sales orders, customer invoices, and user eCommerce contexts.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.normal_partner = cls.env['res.partner'].create({
            'name': 'Test Regular Customer',
            'email': 'regular.customer@example.com',
        })
        cls.blacklisted_partner = cls.env['res.partner'].create({
            'name': 'Test Blacklisted Customer',
            'email': 'blacklisted.customer@example.com',
            'blacklisted_partner': True,
        })

    def test_01_partner_blacklist_toggle(self):
        """Verify partner blacklist flag can be enabled and disabled."""
        partner = self.env['res.partner'].create({
            'name': 'Toggle Customer',
        })
        self.assertFalse(partner.blacklisted_partner)

        partner.write({'blacklisted_partner': True})
        self.assertTrue(partner.blacklisted_partner)

        partner.write({'blacklisted_partner': False})
        self.assertFalse(partner.blacklisted_partner)

    def test_02_sale_order_blacklist_warning(self):
        """Verify sale order displays dynamic warning for blacklisted partners."""
        sale_order = self.env['sale.order'].create({
            'partner_id': self.normal_partner.id,
        })
        self.assertFalse(sale_order.partner_blacklist_warning)

        # Switch to blacklisted customer
        sale_order.write({'partner_id': self.blacklisted_partner.id})
        self.assertTrue(bool(sale_order.partner_blacklist_warning))
        self.assertIn(self.blacklisted_partner.name, sale_order.partner_blacklist_warning)

        # Un-blacklist the partner and verify warning disappears
        self.blacklisted_partner.write({'blacklisted_partner': False})
        sale_order._compute_partner_blacklist_warning()
        self.assertFalse(sale_order.partner_blacklist_warning)

        # Re-blacklist and verify warning reappears
        self.blacklisted_partner.write({'blacklisted_partner': True})
        sale_order._compute_partner_blacklist_warning()
        self.assertTrue(bool(sale_order.partner_blacklist_warning))

    def test_03_account_move_blacklist_warning(self):
        """Verify customer invoice displays warning for blacklisted partners."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.normal_partner.id,
        })
        self.assertFalse(invoice.partner_blacklist_warning)

        # Switch to blacklisted customer
        invoice.write({'partner_id': self.blacklisted_partner.id})
        self.assertTrue(bool(invoice.partner_blacklist_warning))
        self.assertIn(self.blacklisted_partner.name, invoice.partner_blacklist_warning)

        # Un-blacklist customer and verify recompute
        self.blacklisted_partner.write({'blacklisted_partner': False})
        invoice._compute_partner_blacklist_warning()
        self.assertFalse(invoice.partner_blacklist_warning)

        # Re-blacklist customer
        self.blacklisted_partner.write({'blacklisted_partner': True})
        invoice._compute_partner_blacklist_warning()
        self.assertTrue(bool(invoice.partner_blacklist_warning))

    def test_04_user_delegation_blacklist(self):
        """Verify res.users delegates blacklisted_partner from res.partner."""
        test_user = self.env['res.users'].create({
            'name': 'Blacklist Portal User',
            'login': 'blacklist_portal_user',
            'email': 'portal_user@example.com',
            'partner_id': self.blacklisted_partner.id,
        })
        self.assertTrue(test_user.blacklisted_partner)

        self.blacklisted_partner.write({'blacklisted_partner': False})
        self.assertFalse(test_user.blacklisted_partner)
