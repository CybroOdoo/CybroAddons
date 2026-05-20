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


class OilRoyalty(models.Model):
    """
    Manages royalty payments for oil and gas production. Supports both 
    percentage-based revenue and fixed-per-unit calculations, ensuring 
    payments stay within the dates defined by the associated lease agreement.
    """
    _name = 'oil.royalty'
    _description = 'Royalty'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'sequence_royalty'

    name = fields.Char(
        string='Name',
        required=True,
        copy=False,
        help="Descriptive name for this royalty record.")
    sequence_royalty = fields.Char(
        string='Royalty Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help="Auto-generated unique reference number.")

    lease_id = fields.Many2one(
        'oil.lease.agreement',
        string='Lease Agreement',
        required=True,
        tracking=True,
        domain="[('state', '=', 'active')]",
        help="Lease agreement under which this royalty is calculated.")
    lease_expiry_warning = fields.Text(
        string='Lease Expiry Warning',
        compute='_compute_lease_expiry_warning',
        help="Warning if the related lease agreement has expired.")
    lessor_id = fields.Many2one(
        related='lease_id.lessor_id',
        string='Property Owner',
        store=True,
        readonly=False,
        help="Property owner entitled to royalty payments (from lease).")
    notes = fields.Text(string='Notes', help="Enter the notes.")
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        help="Currency for all monetary values in this record.")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help="Select the company.")
    date = fields.Date(
        string='Royalty Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date of this royalty calculation period.")
    royalty_type = fields.Selection(
        [
            ('percentage', 'Percentage of Revenue'),
            ('fixed_per_unit', 'Fixed Per Unit'),
        ],
        string='Royalty Type',
        required=True,
        default='percentage',
        tracking=True,
        help="Method used to calculate royalty: percentage of revenue or fixed per unit.")
    royalty_rate = fields.Float(
        string='Royalty Rate (%)',
        digits=(6, 2),
        default=10.0,
        tracking=True,
        help="Percentage rate when type is 'Percentage of Revenue'. Defaults to 10%.",)
    fixed_rate = fields.Float(
        string='Fixed Rate Per Unit',
        digits=(10, 2),
        tracking=True,
        help="Fixed amount per unit when type is 'Fixed Per Unit'.",)
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('confirmed', 'Confirmed'),
            ('billed', 'Billed'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help="Current workflow status of this royalty record.")
    line_ids = fields.One2many(
        'oil.royalty.line',
        'royalty_id',
        string='Royalty Lines',
        help="Lists the royalty Lines.")
    total_production = fields.Float(
        string='Total Production',
        compute='_compute_totals',
        store=True,
        help="Total production volume aggregated from all lines.")
    total_gross_revenue = fields.Monetary(
        string='Total Gross Revenue',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Total gross revenue aggregated from all lines.")
    total_royalty_amount = fields.Monetary(
        string='Total Royalty Amount',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help="Total royalty payment amount aggregated from all lines.")
    bill_id = fields.Many2one('account.move', string='Associated Bill',
                               readonly=True, copy=False, help="The vendor bill created for this royalty.")
    bill_count = fields.Integer(string='Bill Count', compute='_compute_bill_count',
                                help="Number of associated bills.")

    def _compute_lease_expiry_warning(self):
        """Shows warning if the lease agreement has expired."""
        for record in self:
            if record.lease_id and record.lease_id.state == 'expired':
                record.lease_expiry_warning = _(
                    "Lease Agreement '%s' has expired.",
                    record.lease_id.name)
            else:
                record.lease_expiry_warning = False

    def _compute_bill_count(self):
        """
        Computes the number of bills associated with this royalty record.
        """
        for record in self:
            record.bill_count = 1 if record.bill_id else 0

    @api.constrains('royalty_rate', 'royalty_type')
    def _check_royalty_rate(self):
        """
        Validates that the percentage royalty rate is between 0 and 100.
        """
        for record in self:
            if record.royalty_type == 'percentage':
                if record.royalty_rate <= 0 or record.royalty_rate > 100:
                    raise ValidationError(
                        _("Royalty rate must be between 0 and 100%% for '%s'.",
                          record.sequence_royalty))

    @api.constrains('fixed_rate', 'royalty_type')
    def _check_fixed_rate(self):
        """
        Validates that the fixed per-unit rate is greater than zero.
        """
        for record in self:
            if record.royalty_type == 'fixed_per_unit' and record.fixed_rate <= 0:
                raise ValidationError(
                    _("Fixed rate per unit must be greater than zero for '%s'.",
                      record.sequence_royalty)
                )

    @api.constrains('date')
    def _check_date_not_future(self):
        """
        Ensures the royalty record date is not in the future.
        """
        for record in self:
            if record.date > fields.Date.today():
                raise ValidationError(
                    _("Royalty date cannot be in the future for '%s'.",
                      record.sequence_royalty)
                )

    @api.constrains('date', 'lease_id')
    def _check_date_within_lease(self):
        """
        Validates that the royalty date falls within the start and end dates 
        of the linked lease agreement.
        """
        for record in self:
            lease = record.lease_id
            if lease.start_date and record.date < lease.start_date:
                raise ValidationError(
                    _("Royalty date %s is before the lease start date %s for '%s'.",
                      record.date, lease.start_date, record.sequence_royalty)
                )
            if lease.end_date and record.date > lease.end_date:
                raise ValidationError(
                    _("Royalty date %s is after the lease end date %s for '%s'.",
                      record.date, lease.end_date, record.sequence_royalty)
                )

    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides create to assign a unique sequence reference for each royalty record.
        """
        for vals in vals_list:
            if vals.get('sequence_royalty', _('New')) == _('New'):
                vals['sequence_royalty'] = self.env['ir.sequence'].next_by_code(
                    'oil.royalty') or _('New')
        return super().create(vals_list)

    @api.depends('line_ids.production_volume', 'line_ids.gross_revenue',
                 'line_ids.royalty_amount')
    def _compute_totals(self):
        """
        Aggregates production volumes, revenue, and royalty amounts from lines.
        """
        for record in self:
            record.total_production = sum(
                record.line_ids.mapped('production_volume'))
            record.total_gross_revenue = sum(
                record.line_ids.mapped('gross_revenue'))
            record.total_royalty_amount = sum(
                record.line_ids.mapped('royalty_amount'))

    def action_confirm(self):
        """
        Confirms the royalty record, moving it from 'draft' to 'confirmed'.
        Requires at least one line.
        """
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Only draft royalties can be confirmed."))
            if not record.line_ids:
                raise UserError(
                    _("Add at least one royalty line before confirming."))
            record.write({'state': 'confirmed'})

    def action_create_bill(self):
        """
        Generates a vendor bill (account.move) for the royalty amount and links it.
        """
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed royalties can have bills created."))
        if self.bill_id:
            raise UserError(_("A bill has already been created for this royalty."))

        # Create Bill (Vendor Bill)
        bill_vals = {
            'move_type': 'in_invoice',
            'partner_id': self.lessor_id.id,
            'invoice_date': self.date,
            'currency_id': self.currency_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': f"Royalty Payment for {self.sequence_royalty}",
                'quantity': 1,
                'price_unit': self.total_royalty_amount,
            })],
        }
        bill = self.env['account.move'].create(bill_vals)
        self.write({
            'bill_id': bill.id,
            'state': 'billed'
        })
        return self.action_view_bill()

    def action_view_bill(self):
        """
        Opens the form view of the associated vendor bill.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vendor Bill'),
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': self.bill_id.id,
            'target': 'current',
        }

    def action_mark_paid(self):
        """
        Marks a confirmed royalty record as 'billed' (paid).
        Redirects to bill creation as per user request.
        """
        return self.action_create_bill()

    def action_set_to_draft(self):
        """
        Resets confirmed royalty records back to 'draft' state. 
        Paid records cannot be reset.
        """
        for record in self:
            if record.state == 'billed':
                raise UserError(_("Paid royalties cannot be reset to draft."))
            record.write({'state': 'draft'})


class OilRoyaltyLine(models.Model):
    """
    Individual line items within a royalty record, representing production 
    volume and revenue for a specific product and period.
    """
    _name = 'oil.royalty.line'
    _description = 'Royalty Line'

    royalty_id = fields.Many2one(
        'oil.royalty',
        string='Royalty',
        required=True,
        ondelete='cascade',
        help="Parent royalty record this line belongs to.")
    currency_id = fields.Many2one(
        related='royalty_id.currency_id',
        help="Currency from the parent royalty record.")
    product_id = fields.Many2one('product.product',
                                 'Product',
                                 required=True,
                                 help="Product for which production and revenue are recorded.")
    description = fields.Char(string='Description',
                              help="Description of the production or revenue line item.")
    date = fields.Date(string='Period Date', required=True,
                       help="Production period date for this line.")
    production_volume = fields.Float(
        string='Production Volume',
        digits=(12, 2),
        help="Production quantity in barrels (oil) or MCF (gas).")
    unit_price = fields.Float(
        string='Unit Price',
        digits=(10, 2),
        help="Market price per barrel or MCF.")
    gross_revenue = fields.Monetary(
        string='Gross Revenue',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        help="Gross revenue calculated as volume multiplied by unit price.")
    royalty_amount = fields.Monetary(
        string='Royalty Amount',
        compute='_compute_amounts',
        store=True,
        currency_field='currency_id',
        help="Royalty payment amount calculated based on the royalty type.")

    @api.constrains('production_volume')
    def _check_production_volume(self):
        """
        Ensures production volume is non-negative.
        """
        for line in self:
            if line.production_volume < 0:
                raise ValidationError(
                    _("Production volume cannot be negative.")
                )

    @api.constrains('unit_price')
    def _check_unit_price(self):
        """
        Ensures unit price is non-negative.
        """
        for line in self:
            if line.unit_price < 0:
                raise ValidationError(
                    _("Unit price cannot be negative.")
                )

    @api.constrains('date')
    def _check_line_date(self):
        """
        Ensures line period date is not in the future.
        """
        for line in self:
            if line.date > fields.Date.today():
                raise ValidationError(
                    _("Line period date cannot be in the future.")
                )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Default the unit price from the product's sale price.

        Behaves like a sale order line: the price is pre-filled but the
        user can override it on the line.
        """
        for line in self:
            if line.product_id:
                line.unit_price = line.product_id.lst_price
                if not line.description:
                    line.description = line.product_id.display_name

    @api.depends('production_volume', 'unit_price', 'royalty_id.royalty_type',
                 'royalty_id.royalty_rate', 'royalty_id.fixed_rate')
    def _compute_amounts(self):
        """
        Calculates gross revenue and royalty amount based on the 
        parent's royalty type.
        """
        for line in self:
            line.gross_revenue = line.production_volume * line.unit_price
            if line.royalty_id.royalty_type == 'percentage':
                line.royalty_amount = line.gross_revenue * (
                            line.royalty_id.royalty_rate / 100.0)
            else:
                line.royalty_amount = line.production_volume * line.royalty_id.fixed_rate
