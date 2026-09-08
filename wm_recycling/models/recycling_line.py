# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
#    If not, see <https://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class RecyclingLine(models.Model):
    """One recovered material stream within a recycling order, tracking expected vs. actual yield."""
    _name = 'recycling.line'
    _description = 'Recycling Recovery Line'
    _order = 'order_id, sequence, id'

    @api.model
    def _valid_field_parameter(self, field, name):
        """
        Allow the 'tracking' parameter on recycling line fields so that
        material-level change tracking is supported without Odoo raising an
        unexpected keyword argument warning.
        """
        return name == 'tracking' or super()._valid_field_parameter(field, name)

    sequence = fields.Integer(string='Sequence', default=10)
    order_id = fields.Many2one(
        'recycling.order',
        string='Recycling Order',
        required=True,
        ondelete='cascade',
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='order_id.currency_id',
        store=True, readonly=True,
    )

    # ── What is being recovered ─────────────────────────────────────────────
    product_id = fields.Many2one(
        'product.product',
        string='Recovered Product',
        required=True,
        domain="[('type', '=', 'consu')]",
        help='The sellable/usable product extracted from the waste batch.',
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
    )
    source_product_id = fields.Many2one(
        'product.product',
        string='Source Material/Product',
        related='order_id.product_id',
        store=True, readonly=True,
    )

    # ── Quantities ──────────────────────────────────────────────────────────
    expected_qty = fields.Float(
        string='Target Qty',
        digits=(16, 3),
        help='Estimated recoverable quantity — the target for this material stream.',
    )
    recovered_qty = fields.Float(
        string='Actual Qty',
        digits=(16, 3),
        tracking=True,
        help='Actual quantity recovered during processing.',
    )
    recovery_rate = fields.Float(
        string='Target Achievement (%)',
        compute='_compute_recovery_rate',
        store=True,
        digits=(5, 2),
        help='Actual Qty / Target Qty × 100 — how well this line met its target.',
    )

    # ── Valuation & Sale ────────────────────────────────────────────────────
    sale_price = fields.Monetary(
        string='Sale Price / Unit',
        currency_field='currency_id',
        help='Expected unit sale price for the recovered material.',
    )
    line_value = fields.Monetary(
        string='Est. Line Value',
        compute='_compute_line_value',
        store=True,
        currency_field='currency_id',
    )
    co2_avoided_tons = fields.Float(
        string='Carbon Abated (tCO2e)',
        compute='_compute_co2_avoided_tons',
        store=True,
        digits=(10, 3),
        help='Scope 3 Carbon Abatement (tCO2e avoided) based on EPA WARM standards = (Actual Qty in kg ÷ 1000) × Waste Category EPA WARM Factor.'
    )

    @api.depends('recovered_qty', 'order_id.category_id', 'order_id.category_id.warm_factor_co2')
    def _compute_co2_avoided_tons(self):
        """
        Calculate the estimated CO₂ emissions avoided (in tonnes) by recovering
        this material instead of landfilling, using the configured emissions
        factor per tonne of material.
        """
        for line in self:
            factor = line.order_id.category_id.warm_factor_co2 if line.order_id and line.order_id.category_id else 1.50
            line.co2_avoided_tons = (line.recovered_qty / 1000.0) * factor

    # ── Stock destination ───────────────────────────────────────────────────
    dest_location_id = fields.Many2one(
        'stock.location',
        string='Destination Location',
        domain="[('usage', '=', 'internal')]",
        help='Where the recovered product is moved into stock after completion.',
    )
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        readonly=True, copy=False,
        help='Stock move that adds the recovered product into the destination location.',
    )
    is_stocked = fields.Boolean(
        string='Moved to Stock',
        default=False, readonly=True, copy=False,
    )
    consumption_move_id = fields.Many2one(
        'stock.move',
        string='Consumption Stock Move',
        readonly=True, copy=False,
        help='Stock move that deducts the original waste material from the batch stock location.',
    )
    is_consumed = fields.Boolean(
        string='Waste Consumed from Stock',
        default=False, readonly=True, copy=False,
        help='True once the source waste quantity has been moved out of the batch location.',
    )

    # ── Notes ───────────────────────────────────────────────────────────────
    notes = fields.Text(string='Notes')

    # ── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('recovered_qty', 'expected_qty')
    def _compute_recovery_rate(self):
        """
        Calculate Target Achievement (%) for each recovery line as (actual_qty
        / expected_qty) × 100, measuring how effectively the material recovery
        target was met.
        """
        for line in self:
            if line.expected_qty:
                line.recovery_rate = (
                    line.recovered_qty / line.expected_qty
                ) * 100.0
            else:
                line.recovery_rate = 0.0

    @api.depends('recovered_qty', 'sale_price')
    def _compute_line_value(self):
        """
        Compute the gross monetary value of each recovered material line by
        multiplying the actual recovered quantity by the configured sale price
        per unit.
        """
        for line in self:
            line.line_value = line.recovered_qty * line.sale_price

    # ── Constraints ────────────────────────────────────────────────

    @api.constrains('recovered_qty')
    def _check_total_recovery_qty(self):
        """
        Prevent the sum of recovered quantities across all recovery lines
        from exceeding the parent order's input quantity.          Physically,
        you cannot recover more material than you put in.  This
        constraint fires on every create/write of a recovery line so it cannot
        be bypassed by directly writing a single line.
        """
        for line in self:
            order = line.order_id
            if not order or not order.input_qty:
                continue  # no input reference yet — nothing to enforce

            total_recovered = sum(order.line_ids.mapped('recovered_qty'))
            if total_recovered > order.input_qty:
                raise ValidationError(
                    _(
                        "Total recovered quantity (%(total).3f %(uom)s) exceeds the "
                        "batch input quantity (%(input).3f %(uom)s) on recycling order "
                        "'%(order)s'.\n\n"
                        "Physical recovery cannot exceed 100%% of the input. "
                        "Please correct the recovered quantities."
                    ) % {
                        'total': total_recovered,
                        'input': order.input_qty,
                        'uom': order.input_uom_id.name if order.input_uom_id else '',
                        'order': order.name,
                    }
                )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """
        Pre-populate the unit of measure, expected quantity, and unit sale
        price from the selected recovered product's configuration when the
        product field changes.
        """
        if self.product_id:
            self.uom_id = self.product_id.uom_id
            self.sale_price = self.product_id.list_price

    # ── Stock Movement ───────────────────────────────────────────────────────

    def _move_recovered_stock(self):
        """
        Called by action_done() on the parent order.
        Creates a stock.move from a virtual production location into the
        dest_location_id to book the recovered product into inventory.
        """
        for line in self:
            if line.is_stocked or line.recovered_qty <= 0:
                continue
            if not line.dest_location_id:
                raise UserError(_(
                    "Missing destination stock location for recycling line '%(product)s' on order %(order)s.",
                    product=line.product_id.display_name if line.product_id else '',
                    order=line.order_id.display_name if line.order_id else '',
                ))

            # ── Resolve the shared production/processing location ────────────
            production_loc = self.env.ref(
                'stock.location_production', raise_if_not_found=False
            )
            if not production_loc:
                production_loc = self.env['stock.location'].search(
                    [('usage', '=', 'production')], limit=1
                )
            if not production_loc:
                raise UserError(
                    _("No production location found. "
                      "Please configure a production stock location.")
                )

            order = line.order_id
            batch = order.waste_batch_id
            company_id = self.env.company.id

            # ── 1. Consumption move: batch stock → production location ────────
            # Determine the source waste product and lot from the batch line
            # that matches the recycling order's primary product, or fall back
            # to the first batch line.
            source_batch_line = (
                batch.line_ids.filtered(
                    lambda bl: bl.product_id == order.product_id
                ) or batch.line_ids
            )
            source_batch_line = source_batch_line[0] if source_batch_line else False

            consumption_move = False
            if source_batch_line and batch.location_id:
                source_product = source_batch_line.product_id
                source_uom = source_batch_line.uom_id or source_product.uom_id
                source_lot = source_batch_line.lot_id
                # Use the recovered quantity as the consumption quantity;
                # it represents the waste material converted in this line.
                consume_qty = line.recovered_qty

                consumption_move = self.env['stock.move'].create({
                    'description_picking': _('Waste Consumed: %s → Recycling') % source_product.display_name,
                    'product_id': source_product.id,
                    'product_uom': source_uom.id,
                    'product_uom_qty': consume_qty,
                    'location_id': batch.location_id.id,
                    'location_dest_id': production_loc.id,
                    'origin': order.name,
                    'company_id': company_id,
                })
                consumption_move._action_confirm()
                consumption_move._action_assign()

                for cml in consumption_move.move_line_ids:
                    if source_lot:
                        cml.lot_id = source_lot.id
                    cml.quantity = source_uom._compute_quantity(consume_qty, cml.product_uom_id) if (source_uom and cml.product_uom_id) else consume_qty
                    cml.picked = True
                if not consumption_move.move_line_ids:
                    self.env['stock.move.line'].create({
                        'move_id': consumption_move.id,
                        'product_id': source_product.id,
                        'product_uom_id': source_uom.id,
                        'quantity': consume_qty,
                        'location_id': batch.location_id.id,
                        'location_dest_id': production_loc.id,
                        'lot_id': source_lot.id if source_lot else False,
                        'company_id': company_id,
                        'picked': True,
                    })

                consumption_move._action_done()

            # ── 2. Recovery move: production location → dest_location ─────────
            recovery_move = self.env['stock.move'].create({
                'description_picking': _('Recovered: %s') % line.product_id.display_name,
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id,
                'product_uom_qty': line.recovered_qty,
                'location_id': production_loc.id,
                'location_dest_id': line.dest_location_id.id,
                'origin': line.order_id.name,
                'company_id': self.env.company.id,
            })
            recovery_move._action_confirm()
            recovery_move._action_assign()

            for ml in recovery_move.move_line_ids:
                ml.quantity = line.uom_id._compute_quantity(line.recovered_qty, ml.product_uom_id) if (line.uom_id and ml.product_uom_id) else line.recovered_qty
                ml.picked = True
            if not recovery_move.move_line_ids:
                self.env['stock.move.line'].create({
                    'move_id': recovery_move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': line.uom_id.id,
                    'quantity': line.recovered_qty,
                    'location_id': production_loc.id,
                    'location_dest_id': line.dest_location_id.id,
                    'company_id': self.env.company.id,
                    'picked': True,
                })

            recovery_move._action_done()
            line.write({
                'stock_move_id': recovery_move.id,
                'is_stocked': True,
                'consumption_move_id': consumption_move.id if consumption_move else False,
                'is_consumed': bool(consumption_move),
            })
