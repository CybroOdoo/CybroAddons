# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class OilJVCashCall(models.Model):
    """
    Monthly cash call issued by the operator to JV partners requesting
    advance funding based on their Working Interest. Generates one
    customer invoice per non-operator partner.
    """
    _name = 'oil.jv.cash.call'
    _description = 'JV Cash Call'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_date desc, id desc'

    name = fields.Char(
        string='Cash Call Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated cash call reference.")
    agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JOA',
        required=True,
        tracking=True,
        domain="[('state', '=', 'active')]",
        help="The Joint Operating Agreement for this cash call.")
    afe_id = fields.Many2one(
        'oil.afe',
        string='AFE',
        tracking=True,
        domain="[('agreement_id', '=', agreement_id), "
               "('state', 'in', ['approved', 'in_progress'])]",
        help="Optional: link to a specific AFE.")
    period_date = fields.Date(
        string='Period (Month)',
        required=True,
        tracking=True,
        help="The month/period this cash call covers.")
    due_date = fields.Date(
        string='Due Date',
        required=True,
        tracking=True,
        help="Payment due date for all partners.")
    total_amount = fields.Monetary(
        string='Total Cash Call Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help="Total amount being called from all partners.")
    currency_id = fields.Many2one(
        related='agreement_id.currency_id',
        store=True,
        help="Currency from the parent JOA.")
    company_id = fields.Many2one(
        related='agreement_id.company_id',
        store=True,
        help="Company from the parent JOA.")
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('invoiced', 'Invoiced'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current status of this cash call.")
    line_ids = fields.One2many(
        'oil.jv.cash.call.line',
        'cash_call_id',
        string='Partner Lines',
        help="Breakdown by partner with their WI share.")
    invoice_count = fields.Integer(
        string='Invoice Count',
        compute='_compute_invoice_count',
        help="Number of invoices generated from this cash call.")
    description = fields.Text(
        string='Description',
        help="Description of budgeted expenditure for this period.")
    notes = fields.Text(
        string='Notes',
        help="Additional notes.")
    expiry_warning = fields.Text(
        string='Expiry Warning',
        compute='_compute_expiry_warning',
        help="Warning if related JOA has expired.")

    def _compute_expiry_warning(self):
        """Shows warning if the JOA has expired."""
        for record in self:
            if (record.agreement_id
                    and record.agreement_id.state == 'expired'):
                record.expiry_warning = _(
                    "JV Agreement '%s' has expired.",
                    record.agreement_id.name)
            else:
                record.expiry_warning = False

    def _compute_invoice_count(self):
        """Counts invoices generated from cash call lines."""
        for record in self:
            record.invoice_count = len(
                record.line_ids.mapped('invoice_id').filtered(lambda i: i))

    @api.constrains('total_amount')
    def _check_total_amount(self):
        """Validates total amount is positive."""
        for record in self:
            if record.total_amount <= 0:
                raise ValidationError(
                    _("Total cash call amount must be greater than zero."))

    @api.model_create_multi
    def create(self, vals_list):
        """Assigns auto-sequence on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.jv.cash.call') or _('New')
        return super().create(vals_list)

    @api.onchange('agreement_id', 'total_amount')
    def _onchange_compute_lines(self):
        """Auto-generates partner lines based on JOA working interests."""
        if self.agreement_id and self.total_amount:
            lines = []
            for jv_partner in self.agreement_id.partner_ids:
                partner_share = self.total_amount * (
                    jv_partner.working_interest / 100.0)
                lines.append((0, 0, {
                    'partner_id': jv_partner.partner_id.id,
                    'working_interest': jv_partner.working_interest,
                    'amount': partner_share,
                }))
            self.line_ids = [(5, 0, 0)] + lines

    def action_confirm(self):
        """Confirms the cash call."""
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    _("Only draft cash calls can be confirmed."))
            if not record.line_ids:
                raise UserError(
                    _("Add at least one partner line before confirming."))
            record.write({'state': 'confirmed'})

    def action_generate_invoices(self):
        """
        Generates one customer invoice per partner line for their
        WI share of the cash call amount.
        """
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _("Only confirmed cash calls can generate invoices."))

        invoices_created = 0

        for line in self.line_ids:
            # Skip if already invoiced
            if line.invoice_id:
                continue

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': line.partner_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_date_due': self.due_date,
                'currency_id': self.currency_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': _("Cash Call %s — WI %.2f%%",
                              self.name, line.working_interest),
                    'quantity': 1,
                    'price_unit': line.amount,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            line.write({'invoice_id': invoice.id})
            invoices_created += 1

        if invoices_created:
            self.write({'state': 'invoiced'})
        else:
            raise UserError(
                _("No invoices to create. All partner lines are already "
                  "invoiced."))

        return self.action_view_invoices()

    def action_view_invoices(self):
        """Opens invoices generated from this cash call."""
        self.ensure_one()
        invoice_ids = self.line_ids.mapped('invoice_id').ids
        if not invoice_ids:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cash Call Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'target': 'current',
        }

    def action_set_to_draft(self):
        """Resets cash call to draft."""
        for record in self:
            if record.state == 'invoiced':
                raise UserError(
                    _("Invoiced cash calls cannot be reset to draft."))
            record.write({'state': 'draft'})


class OilJVCashCallLine(models.Model):
    """Individual partner line within a cash call."""
    _name = 'oil.jv.cash.call.line'
    _description = 'Cash Call Partner Line'

    cash_call_id = fields.Many2one(
        'oil.jv.cash.call',
        string='Cash Call',
        required=True,
        ondelete='cascade',
        help="Parent cash call.")
    partner_id = fields.Many2one(
        'res.partner',
        string='JV Partner',
        required=True,
        help="The partner being billed.")
    working_interest = fields.Float(
        string='WI %',
        digits=(6, 4),
        help="Partner's working interest percentage.")
    amount = fields.Monetary(
        string='Call Amount',
        currency_field='currency_id',
        required=True,
        help="Amount being called from this partner.")
    currency_id = fields.Many2one(
        related='cash_call_id.currency_id',
        help="Currency from the parent cash call.")
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        copy=False,
        help="The generated customer invoice.")
    payment_status = fields.Selection(
        related='invoice_id.payment_state',
        string='Payment Status',
        help="Payment status of the linked invoice.")
