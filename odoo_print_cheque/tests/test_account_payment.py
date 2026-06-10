# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#   You can modify it under the terms of the GNU AFFERO
#   GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#   You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#   (AGPL v3) along with this program.
#   If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################from .common import TestChequeCommon
from odoo import fields

class TestAccountPayment(TestChequeCommon):

    def test_account_payment_print_checks(self):
        """Test the print_checks method on account.payment"""
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner.id,
            'amount': 1000,
            'journal_id': self.journal.id,
            'payment_method_line_id': self.payment_method_line_check.id,
            'date': fields.Date.today(),
        })
        
        result = payment.print_checks()
        self.assertEqual(result.get('res_model'), 'cheque.types')
        self.assertEqual(result.get('context').get('default_cheque_date'), payment.date)
        
        # Test PDC
        payment_pdc = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner.id,
            'amount': 2000,
            'journal_id': self.journal.id,
            'payment_method_line_id': self.payment_method_line_pdc.id,
            'date': fields.Date.today(),
            'effective_date': fields.Date.today(),
        })
        result_pdc = payment_pdc.print_checks()
        self.assertEqual(result_pdc.get('context').get('default_cheque_date'), payment_pdc.effective_date)
