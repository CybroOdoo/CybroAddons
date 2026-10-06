# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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

###############################################################################
from odoo.tests.common import TransactionCase
from odoo import Command

class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.partner = cls.env['res.partner'].create({'name': 'Vendor AM'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test AM',
            'type': 'consu',
        })
        cls.move = cls.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': cls.partner.id,
            'invoice_date': '2026-07-08',
            'invoice_line_ids': [
                Command.create({
                    'product_id': cls.product.id,
                    'quantity': 2.0,
                    'price_unit': 100.0,
                }),
                Command.create({
                    'product_id': cls.product.id,
                    'quantity': 3.0,
                    'price_unit': 100.0,
                })
            ]
        })

    def test_compute_amounts_and_words(self):
        """Test compute company currency and words."""
        self.move._compute_amount_total_company_signed()
        self.assertTrue(self.move.amount_total_company_signed > 0)
        
        self.move._compute_number_to_words()
        self.assertTrue(isinstance(self.move.number_to_words, str))

    def test_action_post_merges_lines(self):
        """Test lines are merged on post."""
        self.assertEqual(len(self.move.invoice_line_ids), 2)
        self.move.action_post()
        self.assertEqual(len(self.move.invoice_line_ids), 1)
        self.assertEqual(self.move.invoice_line_ids[0].quantity, 5.0)
