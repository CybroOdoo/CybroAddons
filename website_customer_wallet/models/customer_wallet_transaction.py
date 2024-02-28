# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo.exceptions import ValidationError
from odoo import api, fields, models


class CustomerWalletTransaction(models.Model):
    """Record the transactions of wallet."""
    _name = 'customer.wallet.transaction'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Text(string='Name', help='Name of the transaction',
                       readonly=True, default='New')
    date = fields.Date(string='Date', default=fields.Date.today,
                       help='Date of the transaction')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='Partner of wallet transaction',
                                 required=True)
    amount_type = fields.Selection(
        selection=[('transfer', 'Transferred'),
                   ('added', 'Added')], string='Amount Type',
        help='Type of the amount in wallet.')
    amount = fields.Float(string='Amount', help='Amount in the transaction')

    @api.model
    def create(self, vals):
        """Generate sequence number on creating a record"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'wallet.transaction')
        res = super(CustomerWalletTransaction, self).create(vals)
        return res

    @api.constrains('amount_type')
    def check_amount_type(self):
        """Constraint to check whether the partner has an E-wallet when performing a transfer or adding an amount."""
        for record in self:
            if record.amount_type == 'transfer':
                if not self.env['loyalty.card'].search([('partner_id', '=', record.partner_id.id)]):
                    raise ValidationError(
                        f"{record.partner_id.name} hasn't any E-wallet. Then how can you transfer the amount")
            elif record.amount_type == 'added':
                if not self.env['loyalty.card'].search([('partner_id', '=', record.partner_id.id)]):
                    raise ValidationError(
                        f"{record.partner_id.name} hasn't any E-wallet. Then how can you add the amount")
