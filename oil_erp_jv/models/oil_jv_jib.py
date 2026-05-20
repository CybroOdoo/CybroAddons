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


class OilJVJIB(models.Model):
    """
    Joint Interest Billing (JIB) statement — splits actual costs incurred
    by the operator across JV partners based on their Working Interest.
    Each JIB can reference an AFE and generates partner allocation lines
    automatically.
    """
    _name = 'oil.jv.jib'
    _description = 'Joint Interest Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_date desc, id desc'

    name = fields.Char(
        string='JIB Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated JIB reference.")
    agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JOA',
        required=True,
        tracking=True,
        domain="[('state', '=', 'active')]",
        help="The Joint Operating Agreement for this JIB.")
    afe_id = fields.Many2one(
        'oil.afe',
        string='AFE',
        tracking=True,
        domain="[('agreement_id', '=', agreement_id)]",
        help="Optional: link to a specific AFE for cost tracking.")
    period_date = fields.Date(
        string='Billing Period',
        required=True,
        tracking=True,
        help="The month/period this JIB covers.")
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
            ('billed', 'Billed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current status of this JIB statement.")
    cost_line_ids = fields.One2many(
        'oil.jv.jib.cost.line',
        'jib_id',
        string='Actual Cost Lines',
        help="Actual costs incurred by the operator.")
    allocation_ids = fields.One2many(
        'oil.jv.jib.allocation',
        'jib_id',
        string='Partner Allocations',
        help="Cost allocations to each JV partner by WI%.")
    total_costs = fields.Monetary(
        string='Total Actual Costs',
        compute='_compute_total_costs',
        store=True,
        currency_field='currency_id',
        help="Sum of all actual cost lines.")
    bill_count = fields.Integer(
        string='Bill Count',
        compute='_compute_bill_count',
        help="Number of invoices generated from this JIB.")
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

    @api.depends('cost_line_ids.amount')
    def _compute_total_costs(self):
        """Sums all actual cost line amounts."""
        for record in self:
            record.total_costs = sum(
                record.cost_line_ids.mapped('amount'))

    def _compute_bill_count(self):
        """Counts invoices generated from allocation lines."""
        for record in self:
            record.bill_count = len(
                record.allocation_ids.mapped('invoice_id').filtered(
                    lambda i: i))

    @api.model_create_multi
    def create(self, vals_list):
        """Assigns auto-sequence on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.jv.jib') or _('New')
        return super().create(vals_list)

    def action_compute_allocations(self):
        """
        Splits total actual costs across JV partners based on their
        Working Interest percentages. Clears and regenerates allocation lines.
        """
        for record in self:
            if not record.cost_line_ids:
                raise UserError(
                    _("Add at least one cost line before computing allocations."))
            # Clear existing allocations
            record.allocation_ids.unlink()
            total = record.total_costs
            for jv_partner in record.agreement_id.partner_ids:
                partner_share = total * (
                    jv_partner.working_interest / 100.0)
                self.env['oil.jv.jib.allocation'].create({
                    'jib_id': record.id,
                    'partner_id': jv_partner.partner_id.id,
                    'working_interest': jv_partner.working_interest,
                    'allocated_amount': partner_share,
                })

    def action_confirm(self):
        """Confirms the JIB after computing allocations."""
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    _("Only draft JIBs can be confirmed."))
            if not record.cost_line_ids:
                raise UserError(
                    _("Add cost lines before confirming."))
            if not record.allocation_ids:
                record.action_compute_allocations()
            record.write({'state': 'confirmed'})

    def action_generate_invoices(self):
        """
        Generates customer invoices to all partner allocations for their
        share of actual costs.
        """
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _("Only confirmed JIBs can generate invoices."))

        invoices_created = 0

        for alloc in self.allocation_ids:
            # Skip if already invoiced
            if alloc.invoice_id:
                continue

            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': alloc.partner_id.id,
                'invoice_date': fields.Date.today(),
                'currency_id': self.currency_id.id,
                'invoice_line_ids': [(0, 0, {
                    'name': _("JIB %s — WI %.2f%% of %s",
                              self.name, alloc.working_interest,
                              self.period_date),
                    'quantity': 1,
                    'price_unit': alloc.allocated_amount,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)
            alloc.write({'invoice_id': invoice.id})
            invoices_created += 1

        if invoices_created:
            self.write({'state': 'billed'})
        else:
            raise UserError(
                _("No invoices to create. All partner allocations are "
                  "already billed."))

        return self.action_view_invoices()

    def action_view_invoices(self):
        """Opens invoices generated from this JIB."""
        self.ensure_one()
        invoice_ids = self.allocation_ids.mapped('invoice_id').ids
        if not invoice_ids:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('JIB Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', invoice_ids)],
            'target': 'current',
        }

    def action_set_to_draft(self):
        """Resets JIB to draft."""
        for record in self:
            if record.state == 'billed':
                raise UserError(
                    _("Billed JIBs cannot be reset to draft."))
            record.write({'state': 'draft'})


class OilJVJIBCostLine(models.Model):
    """Actual cost line within a JIB — represents an expense incurred."""
    _name = 'oil.jv.jib.cost.line'
    _description = 'JIB Cost Line'

    jib_id = fields.Many2one(
        'oil.jv.jib',
        string='JIB',
        required=True,
        ondelete='cascade',
        help="Parent JIB statement.")
    currency_id = fields.Many2one(
        related='jib_id.currency_id',
        help="Currency from the parent JIB.")
    cost_category = fields.Selection(
        [
            ('drilling', 'Drilling'),
            ('completion', 'Completion'),
            ('facilities', 'Facilities'),
            ('pipeline', 'Pipeline'),
            ('environmental', 'Environmental'),
            ('geological', 'Geological & Geophysical'),
            ('labor', 'Labor'),
            ('materials', 'Materials & Equipment'),
            ('transportation', 'Transportation'),
            ('overhead', 'Overhead'),
            ('other', 'Other'),
        ],
        string='Cost Category',
        required=True,
        help="Category of the actual cost.")
    description = fields.Char(
        string='Description',
        required=True,
        help="Description of this cost.")
    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        help="Vendor who provided the service/material.")
    bill_reference = fields.Char(
        string='Vendor Bill Ref',
        help="Reference to the original vendor bill.")
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        required=True,
        help="Actual cost amount.")
    account_id = fields.Many2one(
        'account.account',
        string='GL Account',
        help="General ledger account for this cost.")
    date = fields.Date(
        string='Cost Date',
        required=True,
        help="Date the cost was incurred.")

    @api.constrains('amount')
    def _check_amount(self):
        """Validates amount is positive."""
        for line in self:
            if line.amount <= 0:
                raise ValidationError(
                    _("Cost amount must be greater than zero."))


class OilJVJIBAllocation(models.Model):
    """Partner allocation within a JIB — each partner's share of costs."""
    _name = 'oil.jv.jib.allocation'
    _description = 'JIB Partner Allocation'

    jib_id = fields.Many2one(
        'oil.jv.jib',
        string='JIB',
        required=True,
        ondelete='cascade',
        help="Parent JIB statement.")
    partner_id = fields.Many2one(
        'res.partner',
        string='JV Partner',
        required=True,
        help="The partner being allocated costs.")
    working_interest = fields.Float(
        string='WI %',
        digits=(6, 4),
        help="Partner's working interest percentage.")
    allocated_amount = fields.Monetary(
        string='Allocated Amount',
        currency_field='currency_id',
        help="Partner's share of total costs.")
    currency_id = fields.Many2one(
        related='jib_id.currency_id',
        help="Currency from the parent JIB.")
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
