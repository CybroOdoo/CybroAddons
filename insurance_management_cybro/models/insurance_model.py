# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class InsuranceDetails(models.Model):
    _name = 'insurance.details'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    date_start = fields.Date(string='Date Started', default=fields.Date.today(), required=True)
    close_date = fields.Date(string='Date Closed')
    invoice_ids = fields.One2many('account.invoice', 'insurance_id', string='Invoices', readonly=True)
    employee_id = fields.Many2one('employee.details', string='Agent', required=True)
    commission_rate = fields.Float(string='Commission Percentage')
    policy_id = fields.Many2one('policy.details', string='Policy', required=True)
    amount = fields.Float(related='policy_id.amount', string='Amount')
    state = fields.Selection([('draft', 'Draft'), ('confirmed', 'Confirmed'), ('closed', 'Closed')],
                             required=True, default='draft')
    hide_inv_button = fields.Boolean(copy=False)
    note_field = fields.Html(string='Comment')

    @api.multi
    def confirm_insurance(self):
        if self.amount > 0:
            self.state = 'confirmed'
            self.hide_inv_button = True
        else:
            raise UserError(_("Amount should be Greater than Zero"))

    @api.multi
    def create_invoice(self):
        self.env['account.invoice'].create({
            'type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'insurance_id': self.id,
            'origin': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': 'Invoice For Insurance',
                'quantity': 1,
                'price_unit': self.amount,
                'account_id': 41,
            })],
        })
        if self.policy_id.payment_type == 'fixed':
            self.hide_inv_button = False

    @api.multi
    def close_insurance(self):
        for records in self.invoice_ids:
            if records.state == 'paid':
                raise UserError(_("All invoices must be Paid"))
        self.state = 'closed'
        self.hide_inv_button = False

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('insurance.details') or 'New'
        return super(InsuranceDetails, self).create(vals)


class AccountInvoiceRelate(models.Model):
    _inherit = 'account.invoice'

    insurance_id = fields.Many2one('insurance.details', string='Insurance')
    claim_id = fields.Many2one('claim.details', string='Insurance')
