# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Megha (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class AccountMove(models.Model):
    """Alter loan repayment line state on draft and cancel button click"""
    _inherit = 'account.move'

    def button_draft(self):
        """Change repayment record state to 'invoiced'
        while reset to draft the invoice"""
        res = super().button_draft()
        loan_line_ids = self.env['repayment.line'].search([
            ('name', 'ilike', self.payment_reference)])
        if loan_line_ids:
            loan_line_ids.update({
                'state': 'invoiced',
                'invoice': True
            })
        return res

    def button_cancel(self):
        """Change repayment record state to 'unpaid'
        while cancelling the invoice"""
        res = super().button_cancel()
        for record in self:
            loan_line_ids = self.env['repayment.line'].search([
                ('name', 'ilike', record.payment_reference)])
            if loan_line_ids:
                loan_line_ids.update({
                    'state': 'unpaid',
                    'invoice': False
                })
        return res
