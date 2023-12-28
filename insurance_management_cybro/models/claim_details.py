# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys (odoo@cybrosys.com)
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
from odoo import api, fields, models, _


class ClaimDetails(models.Model):
    """This class creates a model 'claim.details' and added fields """
    _name = 'claim.details'
    _description = "Claim Details"

    name = fields.Char(string='Name', copy=False,
                       readonly=True, index=True, default=lambda self: _('New'),
                       help="Sequence for claim details")
    insurance_id = fields.Many2one('insurance.details', required=True,
                                   domain=[('state', '=', 'confirmed')],
                                   string="Insurance",
                                   help="Confirmed orders can be selected")
    partner_id = fields.Many2one(related='insurance_id.partner_id',
                                 string='Customer',
                                 help="Partner related to insurance")
    policy_id = fields.Many2one(related='insurance_id.policy_id',
                                string='Policy',
                                help="Policy related to insurance")
    employee_id = fields.Many2one(related='insurance_id.employee_id',
                                  string='Agent',
                                  help="Employee related to insurance")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="default currency")
    amount = fields.Monetary(related='insurance_id.amount', string='Amount',
                             help="Amount related to insurance")
    date_claimed = fields.Date(
        string='Date Applied', default=fields.Date.context_today,
        help="Date of apply of claim details")
    invoice_id = fields.Many2one('account.move', string='Invoiced',
                                 readonly=True, copy=False,
                                 help="Invoice related to the claim")
    note_field = fields.Html(string='Comment', help="Related notes")

    @api.model
    def create(self, vals):
        """Function to create sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'claim.details') or 'New'
        return super(ClaimDetails, self).create(vals)

    def action_create_bill(self):
        """Function to create bill with corresponding details"""
        if not self.invoice_id:
            invoice_val = self.env['account.move'].sudo().create({
                'move_type': 'in_invoice',
                'invoice_date': fields.Date.context_today(self),
                'partner_id': self.partner_id.id,
                'invoice_user_id': self.env.user.id,
                'claim_id': self.id,
                'invoice_origin': self.name,
                'invoice_line_ids': [(fields.Command.create({
                    'name': 'Invoice For Insurance Claim',
                    'quantity': 1,
                    'price_unit': self.amount,
                    'account_id': 41,
                }))],
            })
            self.invoice_id = invoice_val
