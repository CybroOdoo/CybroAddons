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


class OilJVRevenue(models.Model):
    """
    JV Revenue Distribution — splits net production revenue across JV
    partners based on their Net Revenue Interest (NRI%) or Working
    Interest (WI%) as a fallback. The operator enters production volumes
    and prices, deducts royalties/burdens, and the system allocates net
    revenue to each partner. Generates vendor bills (in_invoice) to pay
    non-operator partners their share.

    This is the revenue-side mirror of Joint Interest Billing (JIB), which
    handles the cost side.
    """
    _name = 'oil.jv.revenue'
    _description = 'JV Revenue Distribution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'period_date desc, id desc'

    name = fields.Char(
        string='Revenue Ref',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated reference number.")
    agreement_id = fields.Many2one(
        'oil.jv.agreement',
        string='JOA',
        required=True,
        tracking=True,
        domain="[('state', '=', 'active')]",
        help="Joint Operating Agreement for this revenue distribution.")
    period_date = fields.Date(
        string='Revenue Period',
        required=True,
        tracking=True,
        help="The month/period this revenue distribution covers.")
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
            ('distributed', 'Distributed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current status of this revenue distribution.")
    revenue_line_ids = fields.One2many(
        'oil.jv.revenue.line',
        'revenue_id',
        string='Revenue Lines',
        help="Production volumes, prices, and deductions.")
    allocation_ids = fields.One2many(
        'oil.jv.revenue.allocation',
        'revenue_id',
        string='Partner Allocations',
        help="Revenue allocations per JV partner.")
    royalty_id = fields.Many2one(
        'oil.royalty',
        string='Royalty Reference',
        domain="[('jv_agreement_id', '=', agreement_id), "
               "('state', 'in', ['confirmed', 'billed'])]",
        help="Link to a confirmed royalty for importing production data.")
    total_gross_revenue = fields.Monetary(
        string='Total Gross Revenue',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Sum of production_volume * unit_price across all lines.")
    total_royalty_deduction = fields.Monetary(
        string='Total Royalty Deduction',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Sum of royalty deductions across all lines.")
    total_other_deductions = fields.Monetary(
        string='Total Other Deductions',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Sum of other deductions (overrides, taxes) across all lines.")
    total_net_revenue = fields.Monetary(
        string='Total Net Revenue',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Net revenue available for distribution to JV partners.")
    bill_count = fields.Integer(
        string='Bill Count',
        compute='_compute_bill_count',
        help="Number of vendor bills generated.")
    notes = fields.Text(
        string='Notes',
        help="Additional notes.")
    expiry_warning = fields.Text(
        string='Expiry Warning',
        compute='_compute_expiry_warning',
        help="Warning if related JOA has expired.")

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------

    def _compute_expiry_warning(self):
        """Shows warning if the JOA has expired."""
        for record in self:
            if (record.agreement_id
                    and record.agreement_id.state == 'expired'):
                record.expiry_warning = _(
                    "JV Agreement '%s' has expired. This distribution "
                    "should not proceed.", record.agreement_id.name)
            else:
                record.expiry_warning = False

    @api.onchange('royalty_id')
    def _onchange_royalty_id(self):
        """Auto-fills agreement and period from the selected royalty."""
        if self.royalty_id:
            if self.royalty_id.jv_agreement_id and not self.agreement_id:
                self.agreement_id = self.royalty_id.jv_agreement_id
            if self.royalty_id.date and not self.period_date:
                self.period_date = self.royalty_id.date

    @api.depends('revenue_line_ids.gross_revenue',
                 'revenue_line_ids.royalty_deduction',
                 'revenue_line_ids.other_deductions',
                 'revenue_line_ids.net_revenue')
    def _compute_totals(self):
        """Sums all monetary fields from revenue lines."""
        for record in self:
            lines = record.revenue_line_ids
            record.total_gross_revenue = sum(
                lines.mapped('gross_revenue'))
            record.total_royalty_deduction = sum(
                lines.mapped('royalty_deduction'))
            record.total_other_deductions = sum(
                lines.mapped('other_deductions'))
            record.total_net_revenue = sum(
                lines.mapped('net_revenue'))

    def _compute_bill_count(self):
        """Counts all vendor bills (partner allocations + royalty bill)."""
        for record in self:
            bills = record.allocation_ids.mapped('bill_id').filtered(
                lambda b: b)
            if record.royalty_id and record.royalty_id.bill_id:
                if record.royalty_id.bill_id not in bills:
                    bills |= record.royalty_id.bill_id
            record.bill_count = len(bills)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        """Assigns auto-sequence on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.jv.revenue') or _('New')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Business actions
    # ------------------------------------------------------------------

    def action_compute_allocations(self):
        """
        Splits total net revenue across JV partners. Uses Net Revenue
        Interest (NRI%) when available, falls back to Working Interest
        (WI%) otherwise. Clears and regenerates allocation lines.

        When a royalty is linked, also adds the lessor (property owner)
        as an allocation line for the royalty deduction amount.
        """
        for record in self:
            if not record.revenue_line_ids:
                raise UserError(
                    _("Add at least one revenue line before computing "
                      "allocations."))

            # Validate total interest % does not exceed 100 for partners
            total_interest = 0.0
            for jv_partner in record.agreement_id.partner_ids:
                if (jv_partner.net_revenue_interest
                        and jv_partner.net_revenue_interest > 0):
                    total_interest += jv_partner.net_revenue_interest
                else:
                    total_interest += jv_partner.working_interest

            if total_interest > 100.0 + 0.01:
                raise UserError(
                    _("Total partner interest (%.4f%%) exceeds 100%%. "
                      "Please correct interests in the JOA before computing allocations.",
                      total_interest))

            # Clear existing allocations
            record.allocation_ids.unlink()
            total = record.total_net_revenue

            for jv_partner in record.agreement_id.partner_ids:
                # Use NRI if set and > 0, otherwise fall back to WI
                if (jv_partner.net_revenue_interest
                        and jv_partner.net_revenue_interest > 0):
                    split_pct = jv_partner.net_revenue_interest
                    interest_type = 'nri'
                else:
                    split_pct = jv_partner.working_interest
                    interest_type = 'wi'
                partner_share = total * (split_pct / 100.0)
                self.env['oil.jv.revenue.allocation'].create({
                    'revenue_id': record.id,
                    'partner_id': jv_partner.partner_id.id,
                    'interest_type': interest_type,
                    'interest_pct': split_pct,
                    'allocated_amount': partner_share,
                })

            if (record.royalty_id
                    and record.royalty_id.lessor_id
                    and record.total_royalty_deduction > 0):
                self.env['oil.jv.revenue.allocation'].create({
                    'revenue_id': record.id,
                    'partner_id': record.royalty_id.lessor_id.id,
                    'interest_type': 'royalty',
                    'interest_pct': 0.0,
                    'allocated_amount': record.total_royalty_deduction,
                    'is_royalty_allocation': True,
                })


    def action_confirm(self):
        """Confirms the revenue distribution after computing allocations."""
        for record in self:
            if record.state != 'draft':
                raise UserError(
                    _("Only draft revenue distributions can be confirmed."))
            if not record.revenue_line_ids:
                raise UserError(
                    _("Add revenue lines before confirming."))
            if not record.allocation_ids:
                record.action_compute_allocations()
            record.write({'state': 'confirmed'})

    def action_generate_bills(self):
        """
        Generates vendor bills (in_invoice) for all revenue allocations.
        Royalty allocations create the lessor bill and also mark the
        linked royalty as billed.
        """
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(
                _("Only confirmed distributions can generate bills."))

        bills_created = 0

        for alloc in self.allocation_ids:
            # Skip if already billed
            if alloc.bill_id:
                continue

            if (alloc.is_royalty_allocation
                    and self.royalty_id
                    and self.royalty_id.bill_id):
                alloc.write({'bill_id': self.royalty_id.bill_id.id})
                bills_created += 1
                continue

            if alloc.is_royalty_allocation:
                invoice_line_vals = {
                    'name': _("Royalty Payment for %s (via %s)",
                              self.royalty_id.sequence_royalty,
                              self.name),
                    'quantity': 1,
                    'price_unit': alloc.allocated_amount,
                }
            else:
                jv_partner = self.agreement_id.partner_ids.filtered(
                    lambda p: p.partner_id == alloc.partner_id)[:1]
                invoice_line_vals = {
                    'name': _("Revenue %s — %s %.2f%% of %s",
                              self.name,
                              alloc.interest_type.upper(),
                              alloc.interest_pct,
                              self.period_date),
                    'quantity': 1,
                    'price_unit': alloc.allocated_amount,
                }
                if jv_partner and jv_partner.jv_revenue_account_id:
                    invoice_line_vals['account_id'] = (
                        jv_partner.jv_revenue_account_id.id)

            bill_vals = {
                'move_type': 'in_invoice',
                'partner_id': alloc.partner_id.id,
                'invoice_date': fields.Date.today(),
                'currency_id': self.currency_id.id,
                'invoice_line_ids': [(0, 0, invoice_line_vals)],
            }
            bill = self.env['account.move'].create(bill_vals)
            alloc.write({'bill_id': bill.id})
            if alloc.is_royalty_allocation and self.royalty_id:
                self.royalty_id.write({
                    'bill_id': bill.id,
                    'state': 'billed',
                })
            bills_created += 1

        if bills_created:
            self.write({'state': 'distributed'})
        else:
            raise UserError(
                _("No bills to create. All allocations are already billed."))

        return self.action_view_bills()

    def action_import_from_royalty(self):
        """
        Convenience: imports production/revenue data from a linked
        royalty record to pre-fill revenue lines.
        """
        self.ensure_one()
        if not self.royalty_id:
            raise UserError(_("Set a Royalty Reference first."))
        if not self.royalty_id.line_ids:
            raise UserError(
                _("The linked royalty has no lines to import."))

        for rline in self.royalty_id.line_ids:
            self.env['oil.jv.revenue.line'].create({
                'revenue_id': self.id,
                'product_id': rline.product_id.id if rline.product_id else False,
                'description': rline.description or _(
                    "Imported from %s",
                    self.royalty_id.sequence_royalty),
                'date': rline.date,
                'production_volume': rline.production_volume,
                'unit_price': rline.unit_price,
                'royalty_deduction': rline.royalty_amount,
            })

    def action_view_bills(self):
        """Opens all vendor bills generated from this revenue distribution,
        including the royalty bill to the lessor."""
        self.ensure_one()
        bill_ids = self.allocation_ids.mapped('bill_id').ids
        # Include the royalty bill if created through this distribution
        if self.royalty_id and self.royalty_id.bill_id:
            royalty_bill = self.royalty_id.bill_id.id
            if royalty_bill not in bill_ids:
                bill_ids.append(royalty_bill)
        if not bill_ids:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Revenue Bills'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', bill_ids)],
            'target': 'current',
        }

    def action_view_royalty(self):
        """Opens the linked royalty record."""
        self.ensure_one()
        if not self.royalty_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'name': _('Royalty'),
            'res_model': 'oil.royalty',
            'view_mode': 'form',
            'res_id': self.royalty_id.id,
            'target': 'current',
        }

    def action_set_to_draft(self):
        """Resets to draft."""
        for record in self:
            if record.state == 'distributed':
                raise UserError(
                    _("Distributed records cannot be reset to draft."))
            record.write({'state': 'draft'})


class OilJVRevenueLine(models.Model):
    """
    Production/revenue line within a JV Revenue Distribution.
    Each line represents production of a specific product type for a
    given date, with gross revenue calculated as volume * price,
    and net revenue after royalty and other deductions.
    """
    _name = 'oil.jv.revenue.line'
    _description = 'JV Revenue Line'

    revenue_id = fields.Many2one(
        'oil.jv.revenue',
        string='Revenue Distribution',
        required=True,
        ondelete='cascade',
        help="Parent revenue distribution record.")
    currency_id = fields.Many2one(
        related='revenue_id.currency_id',
        help="Currency from the parent revenue distribution.")
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        help="Product for this revenue line.")
    description = fields.Char(
        string='Description',
        help="Description of this revenue line.")
    date = fields.Date(
        string='Date',
        required=True,
        help="Production date or sub-period date.")
    production_volume = fields.Float(
        string='Production Volume',
        digits=(12, 2),
        help="Volume produced in the selected unit.")
    uom = fields.Selection(
        [
            ('bbl', 'Barrels'),
            ('mcf', 'MCF'),
            ('boe', 'BOE'),
        ],
        string='Unit',
        default='bbl',
        help="Unit of measurement for production volume.")
    unit_price = fields.Float(
        string='Unit Price',
        digits=(10, 2),
        help="Market price per unit (e.g., $/barrel).")
    gross_revenue = fields.Monetary(
        string='Gross Revenue',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Volume * Unit Price before deductions.")
    royalty_deduction = fields.Monetary(
        string='Royalty Deduction',
        currency_field='currency_id',
        help="Total royalty/burden deduction for this line.")
    other_deductions = fields.Monetary(
        string='Other Deductions',
        currency_field='currency_id',
        help="Other burdens (overriding royalties, production taxes, etc.).")
    net_revenue = fields.Monetary(
        string='Net Revenue',
        currency_field='currency_id',
        compute='_compute_amounts',
        store=True,
        help="Gross Revenue minus all deductions.")

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Pre-fill unit price and description from the product."""
        for line in self:
            if line.product_id:
                line.unit_price = line.product_id.lst_price
                if not line.description:
                    line.description = line.product_id.display_name

    @api.depends('production_volume', 'unit_price',
                 'royalty_deduction', 'other_deductions')
    def _compute_amounts(self):
        """Computes gross revenue and net revenue."""
        for line in self:
            line.gross_revenue = line.production_volume * line.unit_price
            line.net_revenue = (line.gross_revenue
                                - line.royalty_deduction
                                - line.other_deductions)

    @api.constrains('production_volume')
    def _check_production_volume(self):
        for line in self:
            if line.production_volume < 0:
                raise ValidationError(
                    _("Production volume cannot be negative."))

    @api.constrains('unit_price')
    def _check_unit_price(self):
        for line in self:
            if line.unit_price < 0:
                raise ValidationError(
                    _("Unit price cannot be negative."))


class OilJVRevenueAllocation(models.Model):
    """
    Partner allocation within a JV Revenue Distribution.
    Each line represents one partner's share of the net revenue,
    calculated using either NRI% or WI%.
    """
    _name = 'oil.jv.revenue.allocation'
    _description = 'JV Revenue Allocation'

    revenue_id = fields.Many2one(
        'oil.jv.revenue',
        string='Revenue Distribution',
        required=True,
        ondelete='cascade',
        help="Parent revenue distribution record.")
    partner_id = fields.Many2one(
        'res.partner',
        string='JV Partner',
        required=True,
        help="The partner receiving their revenue share.")
    interest_type = fields.Selection(
        [
            ('nri', 'NRI'),
            ('wi', 'WI'),
            ('royalty', 'Royalty'),
        ],
        string='Interest Type',
        help="Whether NRI or WI was used for this allocation.")
    interest_pct = fields.Float(
        string='Interest %',
        digits=(6, 4),
        help="The percentage used to compute this partner's share.")
    allocated_amount = fields.Monetary(
        string='Allocated Amount',
        currency_field='currency_id',
        help="Partner's share of total net revenue.")
    currency_id = fields.Many2one(
        related='revenue_id.currency_id',
        help="Currency from the parent revenue distribution.")
    is_royalty_allocation = fields.Boolean(
        string='Royalty Allocation',
        default=False,
        help="True if this allocation represents the royalty payment "
             "to the lessor (property owner).")
    bill_id = fields.Many2one(
        'account.move',
        string='Vendor Bill',
        readonly=True,
        copy=False,
        help="The generated vendor bill to pay this partner.")
    payment_status = fields.Selection(
        related='bill_id.payment_state',
        string='Payment Status',
        help="Payment status of the linked vendor bill.")
