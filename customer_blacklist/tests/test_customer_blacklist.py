# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
import logging
from odoo.tests.common import TransactionCase, tagged

_logger = logging.getLogger(__name__)


@tagged('post_install', '-at_install')
class TestCustomerBlacklist(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a blacklisted partner
        cls.blacklisted_partner = cls.env['res.partner'].create({
            'name': 'Blacklisted Partner Test',
            'blacklisted_partner': True,
        })
        # Create a normal partner
        cls.normal_partner = cls.env['res.partner'].create({
            'name': 'Normal Partner Test',
            'blacklisted_partner': False,
        })
        _logger.info("--- TestCustomerBlacklist: setUpClass completed. Created blacklisted and normal partners ---")

    def test_sale_order_blacklist_warning(self):
        """Test the blacklist warning compute field on sale.order"""
        _logger.info("--- Starting test_sale_order_blacklist_warning ---")

        # Case 1: Sale Order with a blacklisted partner
        sale_order_blacklisted = self.env['sale.order'].create({
            'partner_id': self.blacklisted_partner.id,
        })
        sale_order_blacklisted._compute_partner_blacklist_warning()
        _logger.info("Sale order warning for blacklisted customer: %s",
                     sale_order_blacklisted.partner_blacklist_warning)
        self.assertEqual(
            sale_order_blacklisted.partner_blacklist_warning,
            f"The {self.blacklisted_partner.name} is marked as blacklisted",
            "Warning message for blacklisted partner should be set on Sale Order"
        )

        # Case 2: Sale Order with a normal partner
        sale_order_normal = self.env['sale.order'].create({
            'partner_id': self.normal_partner.id,
        })
        sale_order_normal._compute_partner_blacklist_warning()
        _logger.info("Sale order warning for normal customer: '%s'", sale_order_normal.partner_blacklist_warning)
        self.assertEqual(
            sale_order_normal.partner_blacklist_warning,
            '',
            "Warning message for normal partner should be empty on Sale Order"
        )

        _logger.info("--- Completed test_sale_order_blacklist_warning successfully ---")

    def test_account_move_blacklist_warning(self):
        """Test the blacklist warning compute field on account.move"""
        _logger.info("--- Starting test_account_move_blacklist_warning ---")

        # Case 1: Account Move with a blacklisted partner
        invoice_blacklisted = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.blacklisted_partner.id,
        })
        invoice_blacklisted._compute_partner_blacklist_warning()
        _logger.info("Invoice warning for blacklisted customer: %s", invoice_blacklisted.partner_blacklist_warning)
        self.assertEqual(
            invoice_blacklisted.partner_blacklist_warning,
            f"The {self.blacklisted_partner.name} is marked as blacklisted",
            "Warning message for blacklisted partner should be set on Invoice"
        )

        # Case 2: Account Move with a normal partner
        invoice_normal = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.normal_partner.id,
        })
        invoice_normal._compute_partner_blacklist_warning()
        _logger.info("Invoice warning for normal customer: '%s'", invoice_normal.partner_blacklist_warning)
        self.assertEqual(
            invoice_normal.partner_blacklist_warning,
            '',
            "Warning message for normal partner should be empty on Invoice"
        )

        _logger.info("--- Completed test_account_move_blacklist_warning successfully ---")
