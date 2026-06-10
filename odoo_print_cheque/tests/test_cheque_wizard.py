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
from odoo.exceptions import UserError
from odoo import fields

class TestChequeWizard(TestChequeCommon):

    def test_cheque_types_wizard_printing(self):
        """Test the cheque.types wizard action_print_selected_cheque"""
        payment = self.env['account.payment'].create({
            'payment_type': 'outbound',
            'partner_type': 'supplier',
            'partner_id': self.partner.id,
            'amount': 1000,
            'journal_id': self.journal.id,
            'payment_method_line_id': self.payment_method_line_check.id,
            'date': fields.Date.today(),
        })
        
        wizard = self.env['cheque.types'].with_context(active_id=payment.id).create({
            'cheque_format_id': self.cheque_format.id,
            'payment_id': payment.id,
            'cheque_date': fields.Date.today(),
            'cheque_amount': 1000,
            'partner_id': self.partner.id,
        })
        
        # Test validation
        wizard_no_format = self.env['cheque.types'].create({'payment_id': payment.id})
        with self.assertRaises(UserError):
            wizard_no_format.action_print_selected_cheque()
            
        result = wizard.action_print_selected_cheque()
        self.assertIn(result.get('type'), ['ir.actions.report', 'ir.actions.act_window'])
        self.assertEqual(payment.is_sent, True)
        
        # Test date formatting (date_remove_slashes=True)
        if result.get('data'):
            self.assertEqual(result.get('data').get('cheque_date'), fields.Date.today().strftime("%d%m%Y"))
        
        # Test date formatting (date_remove_slashes=False)
        self.cheque_format.is_date_remove_slashes = False
        result = wizard.action_print_selected_cheque()
        if result.get('data'):
            self.assertEqual(result.get('data').get('cheque_date'), fields.Date.today().strftime("%d/%m/%Y"))
