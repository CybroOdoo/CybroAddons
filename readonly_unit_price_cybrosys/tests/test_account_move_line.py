# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import TransactionCase


class TestAccountMoveLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.readonly_user = cls.env['res.users'].create({
            'name': 'Readonly Invoice User',
            'login': 'readonly_invoice_user',
            'email': 'readonly_invoice@example.com',
            'readonly_unit_price_invoicing': True,
        })

        cls.normal_user = cls.env['res.users'].create({
            'name': 'Normal Invoice User',
            'login': 'normal_invoice_user',
            'email': 'normal_invoice@example.com',
            'readonly_unit_price_invoicing': False,
        })

        cls.partner = cls.env['res.partner'].create({'name': 'Test Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Product',
            'is_storable': True,
            'list_price': 100.0,
        })

    def test_compute_price_unit_boolean(self):
        """Test the _compute_price_unit_boolean method in account.move.line"""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 1.0,
            })]
        })
        line = invoice.invoice_line_ids[0]

        # Read the computed field as each user. sudo() skips the access
        # checks on the records, while env.user stays the tested user.
        readonly_line = line.with_user(self.readonly_user).sudo()
        self.assertTrue(
            readonly_line.price_unit_boolean,
            "Readonly user should have price_unit_boolean as True "
            "on invoice line")
        normal_line = line.with_user(self.normal_user).sudo()
        self.assertFalse(
            normal_line.price_unit_boolean,
            "Normal user should have price_unit_boolean as False "
            "on invoice line")
