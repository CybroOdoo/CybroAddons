# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Varsha Vivek (odoo@cybrosys.com)
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
#############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError


class AccountMove(models.Model):
    """Inherit account.move model and enable the print option"""
    _inherit = "account.move"

    @api.depends('amount_total')
    def _compute_amount_total_words(self):
        for receipt in self:
            receipt.amount_total_words = receipt.currency_id.amount_to_text(receipt.amount_total)

    amount_total_words = fields.Char("Total (In Words)", compute="_compute_amount_total_words")

    def print_report(self):
        """Method to print report"""
        return self.env.ref(
            'print_voucher_receipts.action_print_receipt').report_action(self, data='')


class VoucherReceiptPrint(models.AbstractModel):
    """Class for print the Qweb report"""
    _name = 'report.print_voucher_receipts.print_voucher_receipt'

    @api.model
    def _get_report_values(self, docids, data):
        for move in self.env['account.move'].search([('id', 'in', docids)]):
            if move.type not in ('in_receipt', 'out_receipt'):
                raise UserError(_("Only receipts could be printed."))
        self.model = self.env.context.get('active_model')
        docs = self.env.context.get('active_ids')
        if docs == None:
            docs = docids
        return {
            'data': self.env['account.move'].search([('id', 'in', docs)])
        }
