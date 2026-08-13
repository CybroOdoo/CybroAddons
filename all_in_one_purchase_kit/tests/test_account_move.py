# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAccountMove(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test Account Move Partner'})
        cls.product = cls.env['product.product'].create({
            'name': 'Test Account Move Product',
            'type': 'consu',
            'list_price': 100.0,
            'standard_price': 80.0,
        })
        cls.journal = cls.env['account.journal'].search([('type', '=', 'purchase')], limit=1)
        if not cls.journal:
            cls.journal = cls.env['account.journal'].create({
                'name': 'Purchase Journal',
                'code': 'POJ',
                'type': 'purchase',
            })

    def test_account_move_company_signed_and_words(self):
        """Test calculation of company signed total and words."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_date': '2026-06-22',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product.id,
                'quantity': 2,
                'price_unit': 150.0,
                'tax_ids': [(5, 0, 0)],
            })],
        })
        move._compute_amount_total_company_signed()
        move._compute_number_to_words()
        self.assertAlmostEqual(move.amount_total, 300.0)
        self.assertAlmostEqual(move.amount_total_company_signed, 300.0)
        self.assertIn('Three Hundred', move.number_to_words)

    def test_account_move_action_post_merging(self):
        """Test that action_post merges lines with same product and price."""
        move = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.partner.id,
            'journal_id': self.journal.id,
            'invoice_date': '2026-06-22',
            'invoice_line_ids': [
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 2,
                    'price_unit': 150.0,
                    'tax_ids': [(5, 0, 0)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 3,
                    'price_unit': 150.0,
                    'tax_ids': [(5, 0, 0)],
                }),
                (0, 0, {
                    'product_id': self.product.id,
                    'quantity': 1,
                    'price_unit': 200.0,
                    'tax_ids': [(5, 0, 0)],
                })
            ],
        })
        self.assertEqual(len(move.invoice_line_ids), 3)
        move.action_post()
        self.assertEqual(len(move.invoice_line_ids), 2)
        merged_line = move.invoice_line_ids.filtered(lambda l: l.price_unit == 150.0)
        other_line = move.invoice_line_ids.filtered(lambda l: l.price_unit == 200.0)
        self.assertEqual(len(merged_line), 1)
        self.assertEqual(merged_line.quantity, 5.0)
        self.assertEqual(other_line.quantity, 1.0)
