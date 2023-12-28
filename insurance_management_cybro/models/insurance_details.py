# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError


class InsuranceDetails(models.Model):
    """This class creates a model 'insurance.details' and added fields """
    _name = 'insurance.details'
    _description = "Insurance Details"

    name = fields.Char(
        string='Name', required=True, copy=False, readonly=True, index=True,
        default=lambda self: _('New'), help="Sequence of insurance created")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True,
                                 help="Partner related to insurance")
    start_date = fields.Date(
        string='Date Started', default=fields.Date.context_today, required=True,
        help="Start date of insurance")
    close_date = fields.Date(string='Date Closed', readonly=True,
                             help="End date of insurance")
    invoice_ids = fields.One2many('account.move', 'insurance_id',
                                  string='Invoices', readonly=True,
                                  help="Invoices related to insurance ")
    employee_id = fields.Many2one(
        'employee.details', string='Agent', required=True,
        help="Agent related to the insurance")
    commission_rate = fields.Float(string='Commission Percentage',
                                   help="Give the commission rate of"
                                        " insurance to the agent",)
    policy_id = fields.Many2one(
        'policy.details', string='Policy', required=True,
        help="Select the policy details and the policy preferred")
    payment_type = fields.Selection(
        [('fixed', 'Fixed'), ('installment', 'Installment')],
        required=True, default='fixed', help="Select the policy type")
    policy_duration = fields.Integer(string='Duration in months', required=True,
                                     help="Specify the policy duration to"
                                          " which this policy exists")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Give the currency")
    amount = fields.Monetary(related='policy_id.amount', string='Amount',
                             help="The amount for the policy based "
                                  "on policy selected")
    amount_installment = fields.Monetary(string="Installment Amount",
                                         compute="_compute_amount",
                                         required=True,
                                         help="Give the installment"
                                              " amount for the policy")
    amount_remaining = fields.Monetary(string='Amount remaining',
                                       compute='_compute_amount_remaining')
    state = fields.Selection(
        [('draft', 'Draft'), ('confirmed', 'Confirmed'), ('closed', 'Closed')],
        required=True, default='draft',
        help="State of insurance")
    hide_inv_button = fields.Boolean(copy=False)
    note_field = fields.Html(string='Comment', help="Give the notes")
    policy_number = fields.Integer(string="Policy Number", required=True,
                                   help="Policy number is a unique number that"
                                        "an insurance company uses to identify"
                                        "you as a policyholder")

    @api.depends('amount', 'policy_duration')
    def _compute_amount(self):
        for record in self:
            if record.policy_duration != 0:
                record.amount_installment = (
                        record.amount / record.policy_duration)
            else:
                record.amount_installment = 0.0

    @api.depends('amount', 'amount_installment', 'invoice_ids.amount_total')
    def _compute_amount_remaining(self):
        for record in self:
            total_invoice_amount = sum(
                record.invoice_ids.mapped('amount_total'))
            total_amount = record.amount
            record.amount_remaining = total_amount - total_invoice_amount

    @api.constrains('commission_rate')
    def _check_commission_rate(self):
        """This function defines a constraint that ensures the '
        commission_rate' attribute of objects meets certain criteria.
        If any object violates the constraint by having a 'commission_rate'
         that falls outside the range of 1 to 100, a validation error
          is raised, """
        if self.filtered(
                lambda reward: (
                        reward.commission_rate < 0 or reward.commission_rate >
                        100)):
            raise ValidationError(
                _('Commission Percentage should be between 1-100'))

    @api.constrains('policy_number')
    def _check_policy_number(self):
        """This function checks if policy number is not added,validation error
        occurs"""
        if not self.policy_number:
            raise ValidationError(
                _('Please add the policy number'))

    def action_confirm_insurance(self):
        """This function creates a validation error if amount not
         greater than zero"""
        if self.amount > 0:
            self.state = 'confirmed'
            self.hide_inv_button = True
        else:
            raise UserError(_("Amount should be greater than zero"))

    def action_create_invoice(self):
        """Function to create invoice with corresponding details"""
        if self.payment_type == 'fixed':
            self.hide_inv_button = False

        created_invoice = self.env['account.move'].sudo().create({
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.context_today(self),
            'partner_id': self.partner_id.id,
            'invoice_user_id': self.env.user.id,
            'invoice_origin': self.name,
            'invoice_line_ids': [(fields.Command.create({
                'name': 'Invoice For Insurance',
                'quantity': 1,
                'price_unit': self.amount if self.payment_type == 'fixed' else
                self.amount_installment,
                'account_id': 41,
            }))],
        })
        self.write({'invoice_ids': [Command.link(created_invoice.id)]})

    def action_close_insurance(self):
        """Function on button to close the paid invoices or else raise
        user error"""
        for records in self.invoice_ids:
            if records.state == 'paid':
                raise UserError(_("All invoices must be paid"))
        self.state = 'closed'
        self.close_date = fields.Date.context_today(self)
        self.hide_inv_button = False

    @api.model
    def create(self, vals):
        """Function to create sequence"""
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'insurance.details') or 'New'
        return super(InsuranceDetails, self).create(vals)
