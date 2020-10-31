# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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

from odoo import models, fields, api, _


class ClaimDetails(models.Model):
    _name = 'claim.details'

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    name_2 = fields.Char(string='Name 2', required=True, copy=False, readonly=True, index=True,
                         default=lambda self: _('New'))
    insurance_id = fields.Many2one('insurance.details', required=True)
    partner_id = fields.Many2one(related='insurance_id.partner_id', string='Customer', readonly=True)
    policy_id = fields.Many2one(related='insurance_id.policy_id', string='Policy', readonly=True)
    employee_id = fields.Many2one(related='insurance_id.employee_id', string='Agent', readonly=True)
    amount = fields.Float(related='insurance_id.amount', string='Amount')
    date_claimed = fields.Date(string='Date Applied', default=fields.Date.today())
    invoice_id = fields.Many2one('account.move', string='Invoiced', readonly=True, copy=False)
    note_field = fields.Html(string='Comment')

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('claim.details') or 'New'
        return super(ClaimDetails, self).create(vals)


    def create_invoice(self):
        if not self.invoice_id:
            invoice_val = self.env['account.move'].create({
                                'move_type': 'in_invoice',
                                'partner_id': self.partner_id.id,
                                'invoice_user_id': self.env.user.id,
                                'claim_id': self.id,
                                'invoice_origin': self.name,
                                'invoice_line_ids': [(0, 0, {
                                    'name': 'Invoice For Insurance Claim',
                                    'quantity': 1,
                                    'price_unit': self.amount,
                                    'account_id': 41,
                                })],
                            })
            self.invoice_id = invoice_val
