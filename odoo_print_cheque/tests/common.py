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
###############################################################################from odoo.tests import TransactionCase

class TestChequeCommon(TransactionCase):

    def setUp(self):
        super(TestChequeCommon, self).setUp()
        self.payment_method_check = self.env['account.payment.method'].search([('name', '=', 'Checks')], limit=1)
        if not self.payment_method_check:
             self.payment_method_check = self.env['account.payment.method'].create({
                'name': 'Checks',
                'code': 'manual_check',
                'payment_type': 'outbound',
            })
            
        self.payment_method_pdc = self.env['account.payment.method'].search([('name', '=', 'PDC')], limit=1)
        if not self.payment_method_pdc:
             self.payment_method_pdc = self.env['account.payment.method'].create({
                'name': 'PDC',
                'code': 'pdc',
                'payment_type': 'outbound',
            })

        self.journal = self.env['account.journal'].create({
            'name': 'Test Bank',
            'type': 'bank',
            'code': 'TBANK',
        })
        
        self.payment_method_line_check = self.env['account.payment.method.line'].create({
            'name': 'Checks',
            'payment_method_id': self.payment_method_check.id,
            'journal_id': self.journal.id,
        })
        
        self.payment_method_line_pdc = self.env['account.payment.method.line'].create({
            'name': 'PDC',
            'payment_method_id': self.payment_method_pdc.id,
            'journal_id': self.journal.id,
        })

        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        
        self.cheque_format = self.env['cheque.format'].create({
            'bank_name': 'Test Bank',
            'cheque_width': 200,
            'cheque_height': 100,
            'is_date_remove_slashes': True,
        })
