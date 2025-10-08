# -*- coding: utf-8 -*-
###############################################################################
#
#   Cybrosys Technologies Pvt. Ltd.
#
#   Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#   Author: Aslam A K( odoo@cybrosys.com )
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
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class ChequeTypes(models.TransientModel):
    """Wizard model to select cheque type."""
    _name = "cheque.types"
    _description = "Cheque Types"

    cheque_format_id = fields.Many2one('cheque.format', string='Cheque Format',
                                       help='Cheque Print Formats')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='Payee Name')
    cheque_amount_in_words = fields.Text(string='Amount in words',
                                         help='Cheque Amount in Words')
    cheque_date = fields.Date(string='Date', help='Cheque Date')
    company_id = fields.Many2one('res.company', string="company",
                                 default=lambda self: self.env.company,
                                 help='Company Name')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  related='company_id.currency_id',
                                  help='Currency')
    cheque_amount = fields.Monetary(currency_field='currency_id',
                                    string='Amount', help='Amount to be paid')
    check_number = fields.Char(string='Check Number', help='Check sequence '
                                                           'Number')
    payment_id = fields.Many2one('account.payment', string='Payment Type',
                                 help='Payment id')

    def action_print_selected_cheque(self):
        """
        Print selected cheque format by calling template.
        """
        if not self.cheque_format_id:
            raise UserError(_("Please select a Cheque Format."))
        self.payment_id.mark_as_sent()
        if self.cheque_format_id.date_remove_slashes:
            cheque_date = self.cheque_date.strftime("%d%m%Y")
        else:
            cheque_date = self.cheque_date.strftime("%d/%m/%Y")
        data = {
            'cheque_width': self.cheque_format_id.cheque_width,
            'cheque_height': self.cheque_format_id.cheque_height,
            'font_size': self.cheque_format_id.font_size,
            'is_account_payee': self.cheque_format_id.is_account_payee,
            'a_c_payee_top_margin': self.cheque_format_id.a_c_payee_top_margin,
            'a_c_payee_left_margin': self.cheque_format_id.a_c_payee_left_margin,
            'a_c_payee_width': self.cheque_format_id.a_c_payee_width,
            'a_c_payee_height': self.cheque_format_id.a_c_payee_height,
            'date_top_margin': self.cheque_format_id.date_top_margin,
            'date_left_margin': self.cheque_format_id.date_left_margin,
            'date_letter_spacing': self.cheque_format_id.date_letter_spacing,
            'beneficiary_top_margin': self.cheque_format_id.beneficiary_top_margin,
            'beneficiary_left_margin': self.cheque_format_id.beneficiary_left_margin,
            'amount_word_tm': self.cheque_format_id.amount_word_tm,
            'amount_word_lm': self.cheque_format_id.amount_word_lm,
            'amount_word_ls': self.cheque_format_id.amount_word_ls,
            'amount_digit_tm': self.cheque_format_id.amount_digit_tm,
            'amount_digit_lm': self.cheque_format_id.amount_digit_lm,
            'amount_digit_ls': self.cheque_format_id.amount_digit_ls,
            'partner': self.partner_id.name,
            'amount_in_words': self.cheque_amount_in_words,
            'amount_in_digit': self.cheque_amount,
            'cheque_date': cheque_date,
            'print_currency': self.cheque_format_id.print_currency,
            'currency_symbol': self.env.company.currency_id.symbol,
            'amount_digit_size': self.cheque_format_id.amount_digit_size,
            'print_cheque_number': self.cheque_format_id.print_cheque_number,
            'check_number': self.check_number,
            'cheque_no_tm': self.cheque_format_id.cheque_no_tm,
            'cheque_no_lm': self.cheque_format_id.cheque_no_lm
        }
        return self.env.ref(
            'odoo_print_cheque.print_cheque_action').report_action(None,
                                                                   data=data)
