# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arwa V V (Contact : odoo@cybrosys.com)
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
from odoo import fields, models


class AccountMove(models.Model):
    """Inherits 'account.move' to add new states"""
    _inherit = 'account.move'

    state = fields.Selection(selection_add=[
        ('first_approval', 'First Approval'),
        ('second_approval', 'Second Approval'), ('posted',)],
        ondelete={'first_approval': 'cascade', 'second_approval': 'cascade'})

    def action_post(self):
        """Method for validating invoices, checks if total amount is greater
            than first validation amount"""
        double_valid = self.env['ir.config_parameter'].sudo().get_param(
            'double_validation_invoice.double_validation')
        first_valid_amt = self.env['ir.config_parameter'].sudo().get_param(
            'double_validation_invoice.first_valid_limit')
        if double_valid:
            if self.state == 'draft' and self.amount_total > float(
                    first_valid_amt):
                self.state = 'first_approval'
            elif (self.state == 'second_approval' or
                  self.state == 'first_approval'):
                return super(AccountMove, self).action_post()
            else:
                return super(AccountMove, self).action_post()
        else:
            return super(AccountMove, self).action_post()

    def action_first_approval(self):
        """Method for first validation of invoice"""
        second_valid_amount = float(
            self.env['ir.config_parameter'].sudo().get_param
            ('double_validation_invoice.second_valid_limit'))
        if self.amount_total > float(second_valid_amount):
            self.state = 'second_approval'
        else:
            self.action_post()

    def action_second_approval(self):
        """Method for second validation of invoice"""
        self.action_post()
