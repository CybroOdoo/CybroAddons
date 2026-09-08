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
from odoo.exceptions import UserError


class RecyclingOrder(models.Model):
    """Groups material recovery lines for a waste batch, tracking yield from intake through stock posting."""
    _name = 'recycling.order'
    _description = 'Recycling Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'name desc'

    # ── Identity ────────────────────────────────────────────────────────────
    name = fields.Char(
        string='Order Reference',
        required=True, copy=False, readonly=True,
        default=lambda self: _('New'),
    )
    waste_batch_id = fields.Many2one(
        'waste.batch',
        string='Waste Batch',
        required=True,
        tracking=True,
        ondelete='restrict',
        domain="[('is_received', '=', True)]",
        help='Only received batches can be recycled.',
    )
    product_id = fields.Many2one(
        'product.product',
        string='Waste Material/Product',
        compute='_compute_product_and_category',
        store=True, readonly=False, precompute=True,
        tracking=True,
        domain="[('is_waste_material', '=', True)]",
        help='Primary material stream being recycled from this batch.'
             ' Pre-filled from the batch lines; can be changed.',
    )
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        compute='_compute_product_and_category',
        store=True, readonly=False, precompute=True,
    )
    hazardous = fields.Boolean(
        related='waste_batch_id.hazardous',
        store=True, readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True, readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
    )

    # ── Scheduling ──────────────────────────────────────────────────────────
    date_start = fields.Date(
        string='Start Date',
        default=fields.Date.today,
        required=True,
        tracking=True,
    )
    date_done = fields.Date(
        string='Completion Date',
        tracking=True,
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user,
        tracking=True,
    )
    facility_location_id = fields.Many2one(
        'stock.location',
        string='Recycling Facility Location',
        domain="[('usage', '=', 'internal')]",
        default=lambda self: self._default_facility_location_id(),
        tracking=True,
    )

    def _default_facility_location_id(self):
        """
        Default recycling facility stock location falling back to the first
        available internal stock location.
        """
        stock_loc = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
        if stock_loc and stock_loc.exists():
            return stock_loc.id
        return self.env['stock.location'].search([('usage', '=', 'internal')], limit=1).id

    # ── Input Quantities ────────────────────────────────────────────────────
    input_qty = fields.Float(
        string='Input Quantity',
        compute='_compute_input_qty',
        store=True, readonly=True,
        digits=(16, 3),
        help='Quantity taken from the waste batch for recycling.',
    )
    input_uom_id = fields.Many2one(
        'uom.uom',
        related='waste_batch_id.uom_id',
        store=True, readonly=True,
    )

    # ── Recovery Lines ──────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'recycling.line',
        'order_id',
        string='Recovery Lines',
    )

    # ── Aggregated Metrics (computed) ────────────────────────────────────────
    total_recovered_qty = fields.Float(
        string='Total Recovered Qty',
        compute='_compute_totals',
        store=True, digits=(16, 3),
    )
    overall_recovery_rate = fields.Float(
        string='Overall Recovery Rate (%)',
        compute='_compute_totals',
        store=True, digits=(5, 2),
        help='Weighted average recovery rate across all lines.',
    )
    total_recovered_value = fields.Monetary(
        string='Est. Recovered Value',
        compute='_compute_totals',
        store=True,
        currency_field='currency_id',
        help='Sum of (recovered qty × sale price) across all lines.',
    )
    co2_avoided_tons = fields.Float(
        string='Carbon Abated (tCO2e)',
        compute='_compute_totals',
        store=True,
        digits=(10, 3),
        help='Scope 3 Carbon Abatement (tCO2e avoided) based on EPA WARM standards = (Total Recovered Qty in kg ÷ 1000) × Waste Category EPA WARM Factor.'
    )

    # ── Sale References ──────────────────────────────────────────────────────
    sale_order_count = fields.Integer(
        string='Sale Orders',
        compute='_compute_sale_count',
    )

    # ── State ────────────────────────────────────────────────────────────────
    state = fields.Selection([
        ('draft',       'Draft'),
        ('confirmed',   'Confirmed'),
        ('in_progress', 'In Progress'),
        ('done',        'Done'),
        ('cancelled',   'Cancelled'),
    ], string='Status', default='draft', required=True,
       tracking=True, copy=False)

    notes = fields.Text(string='Internal Notes')

    # ── Compute Methods ──────────────────────────────────────────────────────

    @api.depends('waste_batch_id.line_ids.remaining_qty', 'waste_batch_id.line_ids.quantity', 'waste_batch_id.batch_type', 'waste_batch_id.status')
    def _compute_input_qty(self):
        """
        Derive the total input quantity from the linked waste batch's received
        quantity, populating the recycling order's source mass figure for yield
        calculation.
        """
        for order in self:
            if order.waste_batch_id and order.waste_batch_id.line_ids:
                batch = order.waste_batch_id
                rem_qty = sum(batch.line_ids.mapped('remaining_qty'))
                if rem_qty <= 0.001 and (batch.batch_type == 'sorted_material' or batch.status == 'sorted'):
                    order.input_qty = sum(batch.line_ids.mapped('quantity'))
                else:
                    order.input_qty = rem_qty
            else:
                order.input_qty = 0.0

    @api.depends('line_ids.recovered_qty', 'line_ids.sale_price',
                 'line_ids.recovery_rate', 'input_qty', 'category_id', 'category_id.warm_factor_co2')
    def _compute_totals(self):
        """
        Aggregate all recovery line quantities and values to compute the
        order's total expected output, total actual recovered weight, gross
        revenue, and overall batch yield percentage.
        """
        for order in self:
            lines = order.line_ids
            total_qty = sum(lines.mapped('recovered_qty'))
            order.total_recovered_qty = total_qty
            if order.input_qty:
                order.overall_recovery_rate = (total_qty / order.input_qty) * 100.0
            else:
                order.overall_recovery_rate = 0.0
            order.total_recovered_value = sum(
                l.recovered_qty * l.sale_price for l in lines
            )
            factor = order.category_id.warm_factor_co2 if order.category_id else 1.50
            order.co2_avoided_tons = (total_qty / 1000.0) * factor

    def _compute_sale_count(self):
        """
        Count the number of sale orders generated from this recycling order's
        recovered product lines, driving the smart button badge on the
        recycling order form.
        """
        SaleOrder = self.env['sale.order']
        valid_orders = [o for o in self if o.name and o.name != _('New')]
        if not valid_orders:
            for order in self:
                order.sale_order_count = 0
            return

        counts = dict(SaleOrder._read_group(
            domain=[('origin', 'in', [o.name for o in valid_orders])],
            groupby=['origin'],
            aggregates=['__count'],
        ))
        for order in self:
            order.sale_order_count = counts.get(order.name, 0)

    # ── ORM ──────────────────────────────────────────────────────────────────

    @api.depends('waste_batch_id', 'waste_batch_id.line_ids.product_id')
    def _compute_product_and_category(self):
        """
        Pre-fill material from the batch's waste composition lines.
        Picks the first hazardous line if any, otherwise the first line.
        """
        for rec in self:
            if not rec.waste_batch_id or not rec.waste_batch_id.line_ids:
                rec.product_id = False
                rec.category_id = False
                continue
            lines = rec.waste_batch_id.line_ids
            haz_lines = lines.filtered('hazardous')
            line = haz_lines[0] if haz_lines else lines[0]
            rec.product_id = line.product_id
            if line.product_id and line.product_id.wm_waste_category_id:
                rec.category_id = line.product_id.wm_waste_category_id.id
            else:
                rec.category_id = False

    @api.onchange('waste_batch_id')
    def _onchange_waste_batch_pre_fill_material(self):
        """
        Pre-fill header material/category AND auto-create recovery lines.
        For every distinct waste material in the batch composition lines we
        look up the matching ``wm.waste.material.sort.config`` record.  If one
        exists its ``dest_product_id``, ``dest_location_id``, and
        ``dest_product_id.list_price`` are used to pre-fill a recovery line.
        Lines are cleared and rebuilt whenever the batch changes so the form
        always reflects the current batch composition.  Materials with no sort
        config are skipped and reported back as a UI warning.
        """
        # ── Always clear existing (unsaved) lines on batch change ────────────
        self.line_ids = [(5, 0, 0)]

        if not self.waste_batch_id:
            self.product_id = False
            self.category_id = False
            return

        batch_lines = self.waste_batch_id.line_ids
        if not batch_lines:
            self.product_id = False
            self.category_id = False
            return

        # ── Pre-fill header fields (primary material) ─────────────────────────
        haz_lines = batch_lines.filtered('hazardous')
        primary_line = haz_lines[0] if haz_lines else batch_lines[0]
        self.product_id = primary_line.product_id
        if primary_line.product_id and primary_line.product_id.wm_waste_category_id:
            self.category_id = primary_line.product_id.wm_waste_category_id.id
        else:
            self.category_id = False

        # ── Build recovery lines from sort config ─────────────────────────────
        # Iterate over distinct materials in the batch to avoid duplicate lines
        # when the same material appears on more than one batch line.
        seen_material_ids = set()
        new_lines = []
        missing_configs = []

        for batch_line in batch_lines:
            material = batch_line.material_id  # product.template
            if not material or material.id in seen_material_ids:
                continue
            seen_material_ids.add(material.id)

            config = self.env['wm.waste.material.sort.config'].search(
                [('material_id', '=', material.id), ('active', '=', True)],
                limit=1,
            )

            if not config:
                missing_configs.append(material.display_name)
                continue

            dest_product = config.dest_product_id
            new_lines.append((0, 0, {
                'product_id': dest_product.id,
                'uom_id': dest_product.uom_id.id,
                'dest_location_id': config.dest_location_id.id,
                'expected_qty': batch_line.remaining_qty or batch_line.quantity,
                'sale_price': dest_product.list_price,
                'notes': config.notes or False,
            }))

        if new_lines:
            self.line_ids = new_lines

        # ── Warn the user about materials with no sort config ─────────────────
        if missing_configs:
            return {
                'warning': {
                    'title': _('Sort Config Missing'),
                    'message': _(
                        'No sort configuration found for the following '
                        'material(s); their recovery lines were not '
                        'pre-filled. Please add them manually or create '
                        'a sort config first:\n\n%s'
                    ) % '\n'.join('\u2022 %s' % m for m in missing_configs),
                }
            }

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to implement custom initialization and validation
        logic.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code('recycling.order')
                    or _('New')
                )
        return super().create(vals_list)

    # ── Workflow Actions ──────────────────────────────────────────────────────

    def _check_recycling_rights(self):
        """
        Verify that the current user has the 'Recycling Operator' or 'Recycling
        Manager' role before allowing state transitions, preventing
        unauthorised processing of waste batches.
        """
        if not (self.env.user.has_group('wm_base.group_wm_recycler') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("Only Recycling Specialists and Operations Managers can manage recycling orders."))

    def action_confirm(self):
        """
        Validate that the recycling order has at least one recovery line and a
        valid facility location, then transition state from 'draft' to
        'confirmed', locking the batch assignment.
        """
        self._check_recycling_rights()
        for order in self:
            if not order.line_ids:
                raise UserError(
                    _("Please add at least one recovery line before confirming.")
                )
            order.write({'state': 'confirmed'})
            if order.waste_batch_id:
                order.waste_batch_id.write({'status': 'sorting'})

    def action_start(self):
        """
        Transition the recycling order to 'in_progress', recording the
        processing start date and notifying the responsible operator to begin
        material recovery operations.
        """
        self._check_recycling_rights()
        for order in self:
            if order.state != 'confirmed':
                raise UserError(_("Only confirmed orders can be started."))
            order.write({'state': 'in_progress'})

    def action_done(self):
        """
        Finalize the recycling order by validating recovered quantities,
        generating stock moves to place recovered materials into inventory, and
        transitioning state to 'done'.
        """
        self._check_recycling_rights()
        for order in self:
            with self.env.cr.savepoint():
                self.env.cr.execute("SELECT id, state FROM recycling_order WHERE id = %s FOR UPDATE", [order.id])
                locked_row = self.env.cr.fetchone()
                if not locked_row or locked_row[1] != 'in_progress' or order.state != 'in_progress':
                    raise UserError(_("Only in-progress orders can be marked as done."))

                if order.waste_batch_id:
                    self.env.cr.execute("SELECT id FROM waste_batch WHERE id = %s FOR UPDATE", [order.waste_batch_id.id])

                lines_without_qty = order.line_ids.filtered(lambda l: not l.recovered_qty)
                if lines_without_qty:
                    raise UserError(
                        _("All recovery lines must have a non-zero recovered quantity before "
                          "closing. Please fill in the recovered quantity for: %s") %
                        ', '.join(lines_without_qty.mapped('product_id.display_name'))
                    )

                # ── Execute stock moves FIRST so failures roll back the state ──────
                # Move 1: Debit waste material from batch location (consumption)
                # Move 2: Credit recovered product into dest location (recovery)
                order.line_ids._move_recovered_stock()

                # ── Move process loss/residue to scrap location if any remaining ────
                residue_qty = order.input_qty - order.total_recovered_qty
                if residue_qty > 0.001 and order.waste_batch_id and order.waste_batch_id.location_id:
                    scrap_loc = self.env.ref('stock.stock_location_scrapped', raise_if_not_found=False)
                    if not scrap_loc:
                        scrap_loc = self.env['stock.location'].search([
                            ('usage', '=', 'inventory'),
                            ('company_id', 'in', [order.company_id.id, False])
                        ], limit=1)
                    product_to_move = order.product_id or (order.waste_batch_id.line_ids and order.waste_batch_id.line_ids[0].product_id)
                    if scrap_loc and product_to_move:
                        order.waste_batch_id._do_internal_move(
                            product=product_to_move,
                            qty=residue_qty,
                            src_loc=order.waste_batch_id.location_id,
                            dest_loc=scrap_loc,
                            origin=_('Process Loss: %s') % order.name,
                        )

                # ── Mark the order and batch done AFTER successful stock moves ─────
                order.write({
                    'state': 'done',
                    'date_done': fields.Date.today(),
                })
                if order.waste_batch_id:
                    order.waste_batch_id.write({'status': 'recycled'})

                # ── Post a traceability summary on the batch chatter ───────────────
                batch = order.waste_batch_id
                consumed_lines = order.line_ids.filtered('is_consumed')
                recovered_lines = order.line_ids.filtered('is_stocked')

                consumed_summary = ', '.join(
                    _('%(qty).3f %(uom)s of %(product)s') % {
                        'qty': line.recovered_qty,
                        'uom': line.order_id.waste_batch_id.uom_id.name or '',
                        'product': line.source_product_id.display_name or _('waste material'),
                    }
                    for line in consumed_lines
                ) or _('(none — batch location not set)')

                recovered_summary = ', '.join(
                    _('%(qty).3f %(uom)s of %(product)s → %(loc)s') % {
                        'qty': line.recovered_qty,
                        'uom': line.uom_id.name,
                        'product': line.product_id.display_name,
                        'loc': line.dest_location_id.display_name if line.dest_location_id else _('no location'),
                    }
                    for line in recovered_lines
                ) or _('(none)')

                batch.message_post(
                    body=_(
                        "<b>Recycling Order %(order)s completed.</b><br/>"
                        "<b>Waste consumed from stock:</b> %(consumed)s<br/>"
                        "<b>Recovered products added to stock:</b> %(recovered)s"
                    ) % {
                        'order': order.name,
                        'consumed': consumed_summary,
                        'recovered': recovered_summary,
                    }
                )

    def action_cancel(self):
        """
        Cancel the recycling order and reverse any pending stock operations,
        releasing the linked waste batch back to 'sorted' state for potential
        re-processing.
        """
        self._check_recycling_rights()
        for order in self:
            if order.state == 'done':
                raise UserError(_("Completed recycling orders cannot be cancelled."))
            order.write({'state': 'cancelled'})
            if order.waste_batch_id:
                order.waste_batch_id.write({'status': 'received'})

    def action_reset_draft(self):
        """
        Restore the recycling order to 'draft' state so operators can correct
        processing parameters, re-assign facilities, or update material
        recovery targets before restarting.
        """
        self._check_recycling_rights()
        for order in self:
            if order.state != 'cancelled':
                raise UserError(_("Only cancelled orders can be reset to draft."))
            order.write({'state': 'draft'})
            if order.waste_batch_id:
                order.waste_batch_id.write({'status': 'received'})

    def action_create_sale_order(self):
        """
        Open a new sale order pre-filled with recovered material lines.
        The user selects the customer directly on the sale order form.
        """
        self._check_recycling_rights()
        self.ensure_one()
        if self.state != 'done':
            raise UserError(_("Only done recycling orders can generate a sale order."))

        existing_so = self.env['sale.order'].search([('origin', '=', self.name), ('state', '!=', 'cancel')], limit=1)
        if existing_so:
            return {
                'name': _('Sale Order — %s') % existing_so.name,
                'type': 'ir.actions.act_window',
                'res_model': 'sale.order',
                'view_mode': 'form',
                'res_id': existing_so.id,
            }

        lines_to_sell = self.line_ids.filtered(
            lambda l: l.recovered_qty > 0 and l.sale_price > 0
        )
        if not lines_to_sell:
            raise UserError(
                _("No recovery lines with quantity and sale price found.")
            )
        return {
            'name': _('New Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_origin': self.name,
                'default_order_line': [(0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.recovered_qty,
                    'product_uom_id': line.uom_id.id,
                    'price_unit': line.sale_price,
                }) for line in lines_to_sell],
            },
        }

    def action_view_sales(self):
        """
        Open the related sale orders generated from this recycling order's
        recovered product lines in a list or form view.
        """
        self.ensure_one()
        sale_orders = self.env['sale.order'].search([('origin', '=', self.name)])
        return {
            'name': _('Sale Orders — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'view_mode': 'list,form',
            'domain': [('id', 'in', sale_orders.ids)],
            'context': {'create': False},
        }

    def action_print_report(self):
        """
        Generate and render the recycling order PDF report, including input
        batch details, recovery line summaries, yield percentages, and stock
        movement results.
        """
        self.ensure_one()
        return self.env.ref(
            'wm_recycling.action_recycling_order_report'
        ).report_action(self)
