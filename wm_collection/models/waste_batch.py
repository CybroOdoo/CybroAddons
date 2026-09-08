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
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class WasteBatchLine(models.Model):
    """One waste stream line inside a batch, recording product, declared weight, and lot assignment."""
    _name = 'waste.batch.line'
    _description = 'Waste Batch Line'
    _order = 'sequence, id'

    batch_id = fields.Many2one(
        'waste.batch',
        string='Batch',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(default=10)
    product_id = fields.Many2one(
        'product.product',
        string='Waste Material/Product',
        required=True,
        domain="[('is_waste_material', '=', True)]",
    )
    material_id = fields.Many2one(
        'product.template',
        string='Waste Material',
        related='product_id.product_tmpl_id',
        store=True,
        readonly=True,
    )
    category_id = fields.Many2one(
        'wm.waste.category',
        string='Category',
        related='product_id.wm_waste_category_id',
        store=True,
        readonly=True,
    )
    hazardous = fields.Boolean(
        string='Hazardous',
        related='product_id.hazardous',
        store=True,
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        digits=(16, 3),
        default=0.0,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='UoM',
    )
    net_weight = fields.Float(
        string='Net Weight (kg)',
        digits=(16, 3),
        compute='_compute_net_weight',
        store=True,
        readonly=False,
    )
    notes = fields.Char(string='Notes')
    lot_id = fields.Many2one(
        'stock.lot',
        string='Stock Lot',
        readonly=True,
        copy=False,
    )

    # ── Sorting ──
    sorted_qty = fields.Float(
        string='Sorted Qty',
        digits=(16, 3),
        default=0.0,
        copy=False,
        help='Cumulative quantity of this line already split out into a '
             'sorted destination batch via the Sort Batch wizard.',
    )
    remaining_qty = fields.Float(
        string='Remaining to Sort',
        compute='_compute_remaining_qty',
        digits=(16, 3),
    )

    @api.depends('quantity', 'uom_id')
    def _compute_net_weight(self):
        """
        Calculate the net weight of the waste batch by subtracting the tare
        weight of all containers from the gross weighed-in quantity, used for
        billing and yield calculations.
        """
        kg_uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        if not kg_uom:
            kg_uom = self.env['uom.uom'].search([('name', 'ilike', 'kg')], limit=1)

        for line in self:
            if line.quantity and line.uom_id:
                try:
                    if kg_uom and line.uom_id._has_common_reference(kg_uom):
                        line.net_weight = line.uom_id._compute_quantity(line.quantity, kg_uom)
                    else:
                        line.net_weight = line.quantity
                except Exception as e:
                    # uom_id may be a NewId on an unsaved line; fall back to raw quantity
                    _logger.debug("Failed to compute quantity with kg_uom for batch line %s: %s", line.id, e)
                    line.net_weight = line.quantity
            else:
                line.net_weight = line.quantity or 0.0

    @api.depends('quantity', 'sorted_qty')
    def _compute_remaining_qty(self):
        """
        Track the unrectested portion of the batch by subtracting quantities
        already allocated to sorted child batches or recycling orders from the
        total received quantity.
        """
        for line in self:
            line.remaining_qty = max(0.0, line.quantity - line.sorted_qty)

    @api.constrains('product_id', 'batch_id')
    def _check_unique_product_per_batch(self):
        """
        Ensure no two material lines within the same waste batch reference the
        same product, preventing quantity double-counting and incorrect yield
        calculations.
        """
        for line in self:
            if line.batch_id and line.product_id:
                duplicate = self.search([
                    ('batch_id', '=', line.batch_id.id),
                    ('product_id', '=', line.product_id.id),
                    ('id', '!=', line.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "The waste product '%(product)s' is added multiple times in batch %(batch)s. Each product can only be added once per batch.",
                        product=line.product_id.display_name,
                        batch=line.batch_id.name or '',
                    ))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Prevent adding lines to a waste batch if the batch is in a final/terminal status.
        """
        for vals in vals_list:
            if vals.get('batch_id') and not self.env.context.get('skip_status_validation') and not self.env.su:
                batch = self.env['waste.batch'].browse(vals['batch_id'])
                if batch.status in ('recycled', 'sold', 'disposed', 'cancel'):
                    raise UserError(_(
                        "Cannot add lines to Waste Batch '%(name)s' because it is in '%(status)s' status.",
                        name=batch.name,
                        status=dict(batch._fields['status'].selection).get(batch.status, batch.status),
                    ))
        return super().create(vals_list)

    def write(self, vals):
        """
        Prevent modifying lines on a waste batch if the batch is in a final/terminal status.
        """
        if not self.env.context.get('skip_status_validation') and not self.env.su:
            for line in self:
                if line.batch_id and line.batch_id.status in ('recycled', 'sold', 'disposed', 'cancel'):
                    raise UserError(_(
                        "Cannot modify line on Waste Batch '%(name)s' because it is in '%(status)s' status.",
                        name=line.batch_id.name,
                        status=dict(line.batch_id._fields['status'].selection).get(line.batch_id.status, line.batch_id.status),
                    ))
        return super().write(vals)

    def unlink(self):
        """
        Prevent deleting lines from a waste batch if the batch is in a final/terminal status.
        """
        if not self.env.context.get('skip_status_validation') and not self.env.su:
            for line in self:
                if line.batch_id and line.batch_id.status in ('recycled', 'sold', 'disposed', 'cancel'):
                    raise UserError(_(
                        "Cannot delete line from Waste Batch '%(name)s' because it is in '%(status)s' status.",
                        name=line.batch_id.name,
                        status=dict(line.batch_id._fields['status'].selection).get(line.batch_id.status, line.batch_id.status),
                    ))
        return super().unlink()


class WasteBatch(models.Model):
    """Master waste intake batch tracking reception, sorting, weight reconciliation, and stock moves."""
    _name = 'waste.batch'
    _description = 'Waste Batch'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']

    name = fields.Char(
        string='Batch Number',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    line_ids = fields.One2many(
        'waste.batch.line',
        'batch_id',
        string='Waste Lines',
        copy=True,
    )

    # ── Inspections ──────────────────────────────────────────────────────────
    inspection_ids = fields.One2many(
        'wm.batch.inspection',
        'batch_id',
        string='Inspections',
    )
    inspection_count = fields.Integer(
        string='Inspection Count',
        compute='_compute_inspection_count',
    )
    inspection_state = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('passed', 'Passed'),
        ('failed', 'Failed')
    ], string='Inspection State', compute='_compute_inspection_state', store=True, default='pending', tracking=True)

    use_batch_inspection = fields.Boolean(compute='_compute_use_settings')
    use_hazardous_waste = fields.Boolean(compute='_compute_use_settings')
    use_batch_approval = fields.Boolean(compute='_compute_use_settings')
    use_batch_labels = fields.Boolean(compute='_compute_use_settings')

    # ── Computed summary fields (for search / filter / reporting) ────────────
    material_ids = fields.Many2many(
        'product.product',
        string='Materials',
        compute='_compute_material_category_ids',
        store=False,
    )
    category_ids = fields.Many2many(
        'wm.waste.category',
        string='Categories',
        compute='_compute_material_category_ids',
        store=False,
    )
    hazardous = fields.Boolean(
        string='Contains Hazardous',
        compute='_compute_hazardous',
        store=True,
        readonly=True,
    )
    quantity = fields.Float(
        string='Quantity',
        compute='_compute_quantity',
        store=False,
        tracking=True
    )
    draft_quantity = fields.Float(
        string='Draft Quantity',
        compute='_compute_draft_quantity',
        store=True,
        digits=(16, 3)
    )
    is_received = fields.Boolean(
        string='Received into Stock',
        default=False,
        copy=False
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        compute='_compute_uom_id',
        store=True,
        readonly=False
    )

    def _default_warehouse_id(self):
        """
        Return the default warehouse for waste batch stock operations from
        company-level settings, ensuring batches are received into the correct
        warehouse location.
        """
        return self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1) or self.env['stock.warehouse'].search([], limit=1)

    def _default_location_id(self):
        """
        Return the configured incoming waste stock location from system
        settings, providing the default destination for new waste batch
        receipts.
        """
        wh = self._default_warehouse_id()
        if wh and wh.lot_stock_id:
            return wh.lot_stock_id
        return self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='warehouse_id.company_id',
        store=True,
        readonly=False,
        default=lambda self: self.env.company,
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        tracking=True,
        default=_default_warehouse_id
    )
    location_id = fields.Many2one(
        'stock.location',
        string='Location',
        required=True,
        tracking=True,
        default=_default_location_id,
        domain="[('usage', '=', 'internal')]"
    )
    received_date = fields.Date(
        string='Received Date',
        default=fields.Date.today,
        required=True,
        tracking=True
    )
    status = fields.Selection([
        ('draft', 'Draft'),
        ('arrived', 'Arrived'),
        ('inspection', 'Inspection'),
        ('received', 'Received'),
        ('sorting', 'Sorting'),
        ('sorted', 'Sorted'),
        ('recycled', 'Recycled'),
        ('disposed', 'Disposed'),
        ('sold', 'Sold'),
    ], string='Status', default='draft', required=True, tracking=True, index=True)

    lot_id = fields.Many2one(
        'stock.lot',
        string='Stock Lot',
        compute='_compute_lot_id',
        readonly=True,
        store=False
    )

    # ── Container / Weighbridge ──────────────────────────────────────────────
    container_type_id = fields.Many2one(
        'wm.container.type',
        string='Container Type',
        tracking=True,
        ondelete='set null',
    )
    container_count = fields.Integer(
        string='Container Count',
        default=1,
    )
    gross_weight = fields.Float(
        string='Gross Weight (kg)',
        digits=(16, 3),
        tracking=True,
    )
    tare_weight = fields.Float(
        string='Tare Weight (kg)',
        digits=(16, 3),
        help='Auto-filled from container type; can be overridden.',
    )
    net_weight = fields.Float(
        string='Net Weight (kg)',
        compute='_compute_net_weight',
        store=True,
        digits=(16, 3),
    )

    # ── Smart-button counters ────────────────────────────────────────────────
    picking_ids = fields.One2many(
        'stock.picking',
        'waste_batch_id',
        string='Stock Pickings',
        copy=False,
    )
    picking_count = fields.Integer(
        string='Pickings',
        compute='_compute_picking_count',
    )

    # ── Sorting / material split traceability ────────────────────────────────
    parent_batch_id = fields.Many2one(
        'waste.batch',
        string='Sorted From',
        readonly=True,
        copy=False,
        index=True,
        help='The mixed batch this single-material batch was split out of '
             'via the Sort Batch wizard, if any.',
    )
    sorted_batch_ids = fields.One2many(
        'waste.batch',
        'parent_batch_id',
        string='Sorted Into',
        copy=False,
    )
    sorted_batch_count = fields.Integer(
        string='Sorted Batches',
        compute='_compute_sorted_batch_count',
    )
    is_fully_sorted = fields.Boolean(
        string='Is Fully Sorted',
        compute='_compute_is_fully_sorted',
        help='True if the batch has been fully sorted into child batches and has no unsorted remaining quantity left.',
    )
    wm_sort_based_on = fields.Selection([
        ('material', 'Waste Material'),
        ('category_and_material', 'Waste Category and Material')
    ], string="Sort Based On", compute="_compute_wm_sort_based_on")

    category_id = fields.Many2one(
        'wm.waste.category',
        string='Waste Category',
        tracking=True,
    )
    intake_weight = fields.Float(
        string='Intake Weight (kg)',
        digits=(16, 3),
        tracking=True,
    )
    intake_date = fields.Datetime(
        string='Intake Date',
        default=fields.Datetime.now,
        tracking=True,
    )
    intake_notes = fields.Text(
        string='Intake Notes',
    )
    weight_variance = fields.Float(
        string='Weight Variance (kg)',
        compute='_compute_weight_variance',
        store=True,
        digits=(16, 3),
    )
    sorting_status = fields.Selection([
        ('unsorted', 'Unsorted'),
        ('in_sorting', 'In Sorting'),
        ('sorted', 'Sorted'),
    ], string='Sorting Status', default='unsorted', tracking=True)
    batch_type = fields.Selection([
        ('collection', 'Collection'),
        ('sorted_material', 'Sorted Material'),
    ], string='Batch Type', default='collection', tracking=True)

    is_category_batch = fields.Boolean(
        string='Is Category Batch',
        default=False,
    )
    is_material_batch = fields.Boolean(
        string='Is Material Batch',
        help="True for child batches produced by a material-level sort. No further sorting is allowed on these.",
        default=False,
    )
    has_multiple_materials = fields.Boolean(
        string='Has Multiple Materials',
        compute='_compute_has_multiple_materials',
        store=False,
        help="True when the batch has lines with more than one distinct waste material.",
    )
    sorting_progress = fields.Float(
        string='Sorting Progress (%)',
        compute='_compute_sorting_progress',
        digits=(5, 1),
        help='Percentage of total batch quantity that has been sorted out '
             'into child batches. Computed from line sorted_qty vs quantity.',
    )

    # ── Aging ────────────────────────────────────────────────────────────────
    days_in_current_status = fields.Integer(
        string='Days Since Received',
        compute='_compute_days_in_current_status',
        store=True,
        aggregator='avg',
        help='Days elapsed since the batch was received.',
    )

    # ────────────────────────────────────────────────────────────────────────
    # Compute methods
    # ────────────────────────────────────────────────────────────────────────

    @api.depends_context('company')
    def _compute_use_settings(self):
        """
        Load batch module feature flags (inspection enforcement, auto-sort
        thresholds, lot tracking) from system configuration to control
        available batch operations.
        """
        params = self.env['ir.config_parameter'].sudo()
        use_insp = params.get_param('wm_collection.use_batch_inspection', 'False') in ('True', '1')
        use_haz = params.get_param('wm_collection.use_hazardous_waste') in ('True', '1')
        use_appr = params.get_param('wm_collection.use_batch_approval') in ('True', '1')
        use_labels = params.get_param('wm_collection.use_batch_labels', 'False') in ('True', '1')
        for rec in self:
            rec.use_batch_inspection = use_insp
            rec.use_hazardous_waste = use_haz
            rec.use_batch_approval = use_appr
            rec.use_batch_labels = use_labels

    def _compute_wm_sort_based_on(self):
        """
        Read the active sorting basis setting (category or material) from
        system configuration and cache it on the batch record, controlling
        which sort wizard mode is shown.
        """
        sort_based_on = self.env['ir.config_parameter'].sudo().get_param(
            'wm_collection.wm_sort_based_on', default='material'
        )
        for rec in self:
            rec.wm_sort_based_on = sort_based_on

    def _compute_sorted_batch_count(self):
        """
        Compute the total number of associated sorted batch records linked to
        this WasteBatch to update smart buttons and summary badges.
        """
        for rec in self:
            rec.sorted_batch_count = len(rec.sorted_batch_ids)

    @api.depends('sorted_batch_ids', 'line_ids.remaining_qty', 'line_ids.quantity')
    def _compute_is_fully_sorted(self):
        """
        Determine whether all material quantities in the batch have been
        allocated to sorted child batches, enabling the 'Move to Stock' action
        when fully sorted.
        """
        for batch in self:
            active_lines = batch.line_ids.filtered(lambda l: l.quantity > 0)
            batch.is_fully_sorted = bool(batch.sorted_batch_ids and active_lines and all(l.remaining_qty <= 0 for l in active_lines))

    @api.depends('line_ids.material_id')
    def _compute_has_multiple_materials(self):
        """
        Flag batches containing more than one distinct waste material product,
        triggering multi-material sort wizard mode instead of the simplified
        single-material auto-sort.
        """
        for rec in self:
            rec.has_multiple_materials = len(rec.line_ids.mapped('material_id')) > 1

    @api.depends('line_ids.sorted_qty', 'line_ids.quantity')
    def _compute_sorting_progress(self):
        """
        Calculate the percentage of the batch quantity already allocated to
        child sorted batches, driving the progress bar indicator on the waste
        batch Kanban and form views.
        """
        for rec in self:
            total = sum(rec.line_ids.mapped('quantity'))
            sorted_total = sum(rec.line_ids.mapped('sorted_qty'))
            if total > 0:
                rec.sorting_progress = min(100.0, (sorted_total / total) * 100.0)
            else:
                rec.sorting_progress = 0.0

    @api.depends('line_ids.product_id')
    def _compute_material_category_ids(self):
        """
        Compile the set of distinct waste categories present across all
        material lines of this batch, used to filter applicable sorting
        configurations and compliance rules.
        """
        for rec in self:
            rec.material_ids = rec.line_ids.mapped('product_id')
            rec.category_ids = rec.line_ids.mapped('category_id')

    @api.depends('line_ids.hazardous')
    def _compute_hazardous(self):
        """
        Automatically flag the waste batch as hazardous if any of its waste
        material lines are classified under a hazardous waste category,
        triggering compliance manifest requirements.
        """
        for rec in self:
            rec.hazardous = any(rec.line_ids.mapped('hazardous'))

    @api.depends('line_ids.product_id', 'line_ids.quantity', 'location_id', 'line_ids.lot_id', 'is_received')
    def _compute_quantity(self):
        """
        Sum all material line quantities to compute the total batch quantity,
        used for displaying aggregate weight on the batch form and in dashboard
        KPIs.
        """
        received = self.filtered('is_received')
        not_received = self - received

        # Batch all stock.quant lookups to avoid N+1 queries
        if received:
            product_ids = received.mapped('line_ids.product_id').ids
            location_ids = received.mapped('location_id').ids
            lot_ids = [lid for lid in received.mapped('line_ids.lot_id').ids if lid]
            domain = [
                ('product_id', 'in', product_ids),
                ('location_id', 'in', location_ids),
            ]
            if lot_ids:
                domain.append(('lot_id', 'in', lot_ids))
            quants = self.env['stock.quant'].search(domain)
            quant_map = {}
            for q in quants:
                key = (q.product_id.id, q.location_id.id, q.lot_id.id)
                quant_map[key] = quant_map.get(key, 0.0) + q.quantity

            for record in received:
                total = 0.0
                for line in record.line_ids:
                    if not line.product_id or not record.location_id or not line.lot_id:
                        continue
                    key = (line.product_id.id, record.location_id.id, line.lot_id.id)
                    total += quant_map.get(key, 0.0)
                record.quantity = total

        for record in not_received:
            record.quantity = sum(record.line_ids.mapped('quantity'))

    @api.depends('line_ids.net_weight', 'line_ids.quantity', 'intake_weight')
    def _compute_draft_quantity(self):
        """
        Calculate the quantity of waste still in draft / unverified state
        within the batch, enabling supervisors to track pending intake
        confirmations.
        """
        for rec in self:
            if rec.line_ids:
                rec.draft_quantity = sum(rec.line_ids.mapped('net_weight'))
            elif rec.intake_weight:
                rec.draft_quantity = rec.intake_weight
            else:
                rec.draft_quantity = 0.0

    @api.depends('intake_weight', 'draft_quantity')
    def _compute_weight_variance(self):
        """
        Compare the declared quantity against the physically weighed quantity
        to compute weight variance, flagging significant discrepancies for
        quality control review.
        """
        for batch in self:
            batch.weight_variance = (batch.intake_weight or 0.0) - (batch.draft_quantity or 0.0)

    @api.constrains('gross_weight', 'tare_weight')
    def _check_gross_tare_weights(self):
        """
        Validate that the tare weight of containers does not exceed the gross
        weighed quantity, raising a ValidationError to prevent logically
        impossible net weight values.
        """
        for batch in self:
            if batch.gross_weight > 0.0 and batch.tare_weight > batch.gross_weight:
                raise ValidationError(_(
                    "Tare weight (%(tare).2f kg) cannot exceed Gross weight (%(gross).2f kg) for Waste Batch '%(name)s'. "
                    "Please verify weighbridge readings or container tare weight.",
                    tare=batch.tare_weight,
                    gross=batch.gross_weight,
                    name=batch.name,
                ))

    @api.depends('line_ids.uom_id')
    def _compute_uom_id(self):
        """
        Derive the unit of measure for the batch from the primary material
        line, ensuring consistent UoM display across batch summary and report
        views.
        """
        kg_uom = self.env.ref('uom.product_uom_kgm', raise_if_not_found=False)
        unit_uom = self.env.ref('uom.product_uom_unit', raise_if_not_found=False)
        for rec in self:
            if rec.line_ids and rec.line_ids[0].uom_id:
                rec.uom_id = rec.line_ids[0].uom_id
            else:
                rec.uom_id = kg_uom or unit_uom

    @api.depends('line_ids.lot_id')
    def _compute_lot_id(self):
        """
        Retrieve the associated stock lot (serial/lot number) generated for
        this batch's stock move, linking physical inventory tracking to the
        waste batch record.
        """
        for rec in self:
            rec.lot_id = rec.line_ids[0].lot_id if rec.line_ids else False

    @api.depends('gross_weight', 'tare_weight')
    def _compute_net_weight(self):
        """
        Calculate the net weight of the waste batch by subtracting the tare
        weight of all containers from the gross weighed-in quantity, used for
        billing and yield calculations.
        """
        for rec in self:
            rec.net_weight = max(0.0, rec.gross_weight - rec.tare_weight)

    @api.depends('picking_ids', 'name', 'is_received')
    def _compute_picking_count(self):
        """
        Count the number of stock picking operations associated with this waste
        batch, driving the Pickings smart button badge on the batch form.
        """
        for rec in self:
            if rec.picking_ids:
                rec.picking_count = len(rec.picking_ids)
            elif rec.name and rec.name != _('New'):
                rec.picking_count = self.env['stock.picking'].search_count(['|', ('waste_batch_id', '=', rec.id), ('origin', '=', rec.name)])
            else:
                rec.picking_count = 0

    @api.depends('received_date')
    def _compute_days_in_current_status(self):
        """
        Count the number of calendar days the waste batch has remained in its
        current state (e.g. days awaiting inspection), supporting SLA
        monitoring and escalation alerts.
        """
        today = fields.Date.today()
        for rec in self:
            rec.days_in_current_status = (today - rec.received_date).days if rec.received_date else 0

    @api.depends('inspection_ids.state')
    def _compute_inspection_count(self):
        """
        Compute the total number of associated inspection records linked to
        this WasteBatch to update smart buttons and summary badges.
        """
        for rec in self:
            rec.inspection_count = len(rec.inspection_ids)

    @api.depends('inspection_ids.state')
    def _compute_inspection_state(self):
        """
        Derive the aggregate inspection state of the waste batch from its
        linked inspection records, showing 'passed', 'failed', 'pending', or
        'not_required' on the batch form.
        """
        for rec in self:
            states = rec.inspection_ids.mapped('state')
            if 'passed' in states:
                rec.inspection_state = 'passed'
            elif 'failed' in states:
                rec.inspection_state = 'failed'
            elif 'in_progress' in states:
                rec.inspection_state = 'in_progress'
            else:
                rec.inspection_state = 'pending'

    # ────────────────────────────────────────────────────────────────────────
    # Onchange methods
    # ────────────────────────────────────────────────────────────────────────

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Update the default receiving stock location and associated picking type
        when the warehouse changes, keeping location defaults aligned with the
        selected warehouse's configuration.
        """
        if self.warehouse_id:
            self.location_id = self.warehouse_id.lot_stock_id

    @api.onchange('container_type_id', 'container_count')
    def _onchange_container_type(self):
        """
        Pre-fill the tare weight field from the selected container type's
        default tare, reducing manual entry and improving net weight accuracy
        for batch intake.
        """
        if self.container_type_id:
            self.tare_weight = (
                self.container_type_id.default_tare_weight * (self.container_count or 1)
            )

    @api.onchange('line_ids')
    def _onchange_lines_hazardous_container(self):
        """
        Soft guide: if any line is hazardous and the container type is not
        marked as hazardous-suitable, clear it with a warning.
        """
        if not self.container_type_id:
            return
        has_hazardous = any(self.line_ids.mapped('hazardous'))
        if has_hazardous and not self.container_type_id.is_hazardous_suitable:
            old_name = self.container_type_id.name
            self.container_type_id = False
            return {
                'warning': {
                    'title': _('Container Type Cleared'),
                    'message': _(
                        '"%s" is not marked as suitable for hazardous waste. '
                        'The container type has been cleared. Please select a '
                        'hazardous-appropriate container (e.g. Drum, IBC Tote), '
                        'or manually re-select it if needed.'
                    ) % old_name,
                }
            }

    # ────────────────────────────────────────────────────────────────────────
    # ORM overrides
    # ────────────────────────────────────────────────────────────────────────

    def _assign_stock_lot(self):
        """
        Ensure a stock lot exists and is assigned to each batch line for its
        specific product.
        """
        for batch in self:
            if not batch.line_ids:
                continue

            company_id = batch.warehouse_id.company_id.id or self.env.company.id
            lines_to_assign = []
            lot_names_to_search = set()
            product_ids = set()

            multi_products = len(set(batch.line_ids.mapped('product_id').ids)) > 1

            for idx, line in enumerate(batch.line_ids, start=1):
                if not line.product_id:
                    continue
                if line.lot_id and line.lot_id.product_id != line.product_id:
                    line.lot_id = False
                if not line.lot_id:
                    lot_name = f"{batch.name}/{idx}" if multi_products else batch.name
                    lines_to_assign.append((line, lot_name))
                    lot_names_to_search.add(lot_name)
                    lot_names_to_search.add(batch.name)
                    product_ids.add(line.product_id.id)

            if not lines_to_assign:
                continue

            existing_lots = self.env['stock.lot'].search([
                ('name', 'in', list(lot_names_to_search)),
                ('product_id', 'in', list(product_ids)),
                ('company_id', '=', company_id),
            ])
            lot_dict = {(lot.name, lot.product_id.id): lot for lot in existing_lots}

            for line, lot_name in lines_to_assign:
                prod_id = line.product_id.id
                lot = lot_dict.get((lot_name, prod_id)) or lot_dict.get((batch.name, prod_id))
                if not lot:
                    lot = self.env['stock.lot'].create({
                        'name': lot_name,
                        'product_id': prod_id,
                        'company_id': company_id,
                    })
                    lot_dict[(lot_name, prod_id)] = lot
                line.lot_id = lot.id

    @api.model_create_multi
    def create(self, vals_list):
        """ Override create to implement custom initialization and validation logic. """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('waste.batch') or _('New')

        batches = super(WasteBatch, self).create(vals_list)
        batches._assign_stock_lot()

        return batches

    LEGAL_STATUS_TRANSITIONS = {
        'draft': {'inspection', 'arrived', 'received', 'cancel', 'disposed'},
        'inspection': {'draft', 'arrived', 'received', 'disposed', 'cancel'},
        'arrived': {'inspection', 'received', 'sorting', 'sorted', 'disposed', 'cancel'},
        'received': {'sorting', 'sorted', 'recycled', 'sold', 'disposed', 'cancel'},
        'sorting': {'sorted', 'recycled', 'received', 'sold', 'disposed', 'cancel'},
        'sorted': {'sorting', 'recycled', 'sold', 'disposed', 'cancel'},
        'recycled': set(),
        'sold': set(),
        'disposed': set(),
        'cancel': {'draft'},
    }

    def write(self, vals):
        """ Override write to implement business validations and side effects. """
        if not self.env.context.get('skip_status_validation') and not self.env.su:
            restricted_fields = {
                'category_id', 'line_ids', 'warehouse_id', 'location_id',
                'intake_weight', 'intake_date', 'draft_quantity',
                'container_type_id', 'container_count', 'gross_weight', 'tare_weight',
                'intake_notes', 'received_date', 'net_weight', 'notes',
            }
            if restricted_fields.intersection(vals.keys()):
                for batch in self:
                    if batch.status in ('recycled', 'sold', 'disposed', 'cancel'):
                        raise UserError(_(
                            "Cannot modify Waste Batch '%(name)s' because it is in '%(status)s' status.",
                            name=batch.name,
                            status=dict(self._fields['status'].selection).get(batch.status, batch.status),
                        ))

        if 'status' in vals and not self.env.context.get('skip_status_validation'):
            new_status = vals['status']
            for batch in self:
                if batch.status and batch.status != new_status:
                    allowed = self.LEGAL_STATUS_TRANSITIONS.get(batch.status, set())
                    if new_status not in allowed:
                        raise ValidationError(_(
                            "Illegal status transition for Waste Batch '%(name)s': Cannot transition from '%(old)s' to '%(new)s'.",
                            name=batch.name,
                            old=dict(self._fields['status'].selection).get(batch.status, batch.status),
                            new=dict(self._fields['status'].selection).get(new_status, new_status),
                        ))

        if vals.get('is_received') and not self.env.context.get('skip_stock_check'):
            for batch in self:
                if not batch.is_received and not batch.picking_ids and not batch.parent_batch_id:
                    raise ValidationError(_(
                        "Cannot directly mark Waste Batch '%(name)s' as received without executing stock movements (use Move to Stock).",
                        name=batch.name,
                    ))

        res = super(WasteBatch, self).write(vals)
        if 'status' in vals and vals['status'] in ('recycled', 'disposed', 'sold'):
            for batch in self:
                if batch.parent_batch_id and batch.parent_batch_id.status not in ('recycled', 'disposed', 'sold'):
                    parent = batch.parent_batch_id
                    if parent.sorted_batch_ids and all(child.status in ('recycled', 'disposed', 'sold') for child in parent.sorted_batch_ids):
                        if all(c.status == 'recycled' for c in parent.sorted_batch_ids):
                            target_status = 'recycled'
                        elif all(c.status == 'disposed' for c in parent.sorted_batch_ids):
                            target_status = 'disposed'
                        elif all(c.status == 'sold' for c in parent.sorted_batch_ids):
                            target_status = 'sold'
                        else:
                            target_status = 'disposed'
                        parent.write({'status': target_status, 'sorting_status': 'sorted'})
        return res

    def unlink(self):
        """ Prevent deletion of received or finalized waste batches. """
        for batch in self:
            if batch.status not in ('draft', 'cancel') or batch.is_received:
                raise UserError(_(
                    "Cannot delete Waste Batch '%(name)s' because it is in '%(status)s' status.",
                    name=batch.name,
                    status=dict(self._fields['status'].selection).get(batch.status, batch.status),
                ))
        return super().unlink()

    # ────────────────────────────────────────────────────────────────────────
    # Action helpers (smart buttons)
    # ────────────────────────────────────────────────────────────────────────

    def action_view_lot(self):
        """
        Open the stock lot record linked to this waste batch's inventory move,
        allowing users to inspect lot tracking details and trace material
        movement.
        """
        self.ensure_one()
        lots = self.line_ids.mapped('lot_id')
        if not lots:
            raise UserError(_("No stock lot is assigned to this batch."))
        action = {
            'name': _('Lots — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'domain': [('id', 'in', lots.ids)],
            'context': {'create': False},
        }
        if len(lots) == 1:
            action.update({'view_mode': 'form', 'res_id': lots.id})
        else:
            action.update({'view_mode': 'list,form'})
        return action

    def action_view_pickings(self):
        """
        Open the list of all stock picking operations (receipts, internal
        transfers) created from this waste batch for inventory traceability.
        """
        self.ensure_one()
        pickings = self.picking_ids or self.env['stock.picking'].search(['|', ('waste_batch_id', '=', self.id), ('origin', '=', self.name)])
        action = {
            'name': _('Transfers — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'view_mode': 'list,form',
            'domain': [('id', 'in', pickings.ids)],
            'context': {'create': False},
        }
        if len(pickings) == 1:
            action.update({'view_mode': 'form', 'res_id': pickings.id})
        return action

    def action_view_inspections(self):
        """
        Open the list of waste batch inspection records linked to this batch,
        allowing quality managers to review inspection results, photos, and
        pass/fail decisions.
        """
        self.ensure_one()
        return {
            'name': _('Inspections — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'wm.batch.inspection',
            'view_mode': 'list,form',
            'domain': [('batch_id', '=', self.id)],
            'context': {'default_batch_id': self.id},
        }

    # ────────────────────────────────────────────────────────────────────────
    # Workflow actions
    # ────────────────────────────────────────────────────────────────────────

    def action_receive_batch(self):
        """
        Step 1 — Log Arrival: register that the batch has physically arrived.
        Assigns stock lots and sets status to Arrived. No stock picking is
        created here.
        """
        self.ensure_one()
        if not (self.env.user.has_group('wm_base.group_wm_inventory_operator') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("Only Inventory & Yard Operators and Operations Managers can receive batches."))
        if not self.env.context.get('skip_inspection_check') and self.use_batch_inspection:
            has_passed = (self.inspection_state == 'passed') or bool(
                self.env['wm.batch.inspection'].search_count([
                    ('batch_id', '=', self.id),
                    ('state', '=', 'passed')
                ])
            ) or any(insp.state == 'passed' for insp in self.inspection_ids)
            if not has_passed:
                raise UserError(_("This batch requires inspection before it can be received into inventory. Please start and complete inspection first."))

        if self.status not in ('draft', 'inspection'):
            raise UserError(_("Only draft batches can be marked as arrived."))
        if not any(l.quantity > 0 for l in self.line_ids):
            raise UserError(_("Add at least one batch line with a quantity greater than zero."))
        for line in self.line_ids:
            if not line.product_id.is_storable:
                line.product_id.sudo().write({'is_storable': True})
        self._assign_stock_lot()
        self.write({'status': 'arrived'})

    def action_move_to_stock(self):
        """
        Step 2 — Move to Stock: create and validate the stock picking so waste
        enters physical inventory. Sets is_received=True and status to
        Received.         Blocked by the inspection approval gate when that
        setting is enabled.
        """
        self.ensure_one()
        if not (self.env.user.has_group('wm_base.group_wm_inventory_operator') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("Only Inventory & Yard Operators and Operations Managers can move batches to stock."))

        # Row-level DB lock to guarantee idempotency and prevent concurrent double-moves
        self.env.cr.execute("SELECT id, is_received FROM waste_batch WHERE id = %s FOR UPDATE", [self.id])
        locked_row = self.env.cr.fetchone()
        if not locked_row or locked_row[1] or self.is_received:
            raise UserError(_("This waste batch has already been received into stock."))

        if not self.env.context.get('skip_inspection_check') and self.use_batch_inspection:
            has_passed = (self.inspection_state == 'passed') or bool(
                self.env['wm.batch.inspection'].search_count([
                    ('batch_id', '=', self.id),
                    ('state', '=', 'passed')
                ])
            ) or any(insp.state == 'passed' for insp in self.inspection_ids)
            if not has_passed:
                raise UserError(_("This batch requires inspection before it can be received into inventory. Please start and complete inspection first."))

        use_appr = self.env['ir.config_parameter'].sudo().get_param('wm_collection.use_batch_approval') == 'True'
        if use_appr and self.inspection_state != 'passed':
            raise ValidationError(_("Cannot move to stock: Inspection must be Passed first."))

        if not self.line_ids and self.category_id and (self.intake_weight or self.draft_quantity):
            product = self.env['product.product'].search([
                ('wm_waste_category_id', '=', self.category_id.id),
                ('is_waste_material', '=', True)
            ], limit=1)
            if not product:
                product = self.env['product.product'].sudo().create({
                    'name': self.category_id.name,
                    'is_waste_material': True,
                    'wm_waste_category_id': self.category_id.id,
                    'is_storable': True,
                })
            self.env['waste.batch.line'].create({
                'batch_id': self.id,
                'product_id': product.id,
                'quantity': self.intake_weight or self.draft_quantity or 1.0,
                'category_id': self.category_id.id,
            })

        if not self.line_ids:
            raise UserError(_(
                "Cannot move Waste Batch '%(name)s' to stock: The batch contains no waste lines. "
                "Please add at least one line with a product and quantity before receiving into stock.",
                name=self.name,
            ))

        qty_by_line = {line: line.quantity for line in self.line_ids if line.quantity > 0.0}
        for line in self.line_ids:
            if line.product_id and not line.product_id.is_storable:
                line.product_id.write({'is_storable': True})
        self._assign_stock_lot()

        supplier_loc = self.env['stock.location'].search([('usage', '=', 'supplier')], limit=1)
        if not supplier_loc:
            supplier_loc = self.env.ref('stock.stock_location_suppliers', raise_if_not_found=False)
        if not supplier_loc:
            supplier_loc = self.env['stock.location'].create({
                'name': 'Virtual Supplier Location',
                'usage': 'supplier',
            })

        picking_type = self.warehouse_id.in_type_id or self.env['stock.picking.type'].search([
            ('warehouse_id', '=', self.warehouse_id.id),
            ('code', '=', 'incoming')
        ], limit=1)

        picking = self.env['stock.picking'].with_context(default_batch_id=False).create({
            'waste_batch_id': self.id,
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': supplier_loc.id,
            'location_dest_id': self.location_id.id,
            'origin': self.name,
            'company_id': self.warehouse_id.company_id.id or self.env.company.id,
        })

        line_to_move_map = {}
        for line, qty in qty_by_line.items():
            move = self.env['stock.move'].create({
                'product_id': line.product_id.id,
                'product_uom': line.uom_id.id or line.product_id.uom_id.id or self.uom_id.id,
                'product_uom_qty': qty,
                'location_id': supplier_loc.id,
                'location_dest_id': self.location_id.id,
                'picking_id': picking.id,
                'origin': self.name,
                'company_id': self.warehouse_id.company_id.id or self.env.company.id,
            })
            line_to_move_map[line] = move

        picking.action_confirm()
        picking.action_assign()

        for line, move in line_to_move_map.items():
            qty = qty_by_line[line]
            line_uom = line.uom_id or line.product_id.uom_id
            if move.move_line_ids:
                for ml in move.move_line_ids:
                    converted_qty = line_uom._compute_quantity(qty, ml.product_uom_id) if (line_uom and ml.product_uom_id) else qty
                    ml.write({
                        'lot_id': line.lot_id.id if line.lot_id else False,
                        'quantity': converted_qty,
                        'picked': True,
                    })
            else:
                converted_qty = line_uom._compute_quantity(qty, move.product_uom) if (line_uom and move.product_uom) else qty
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': line.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': converted_qty,
                    'location_id': supplier_loc.id,
                    'location_dest_id': self.location_id.id,
                    'lot_id': line.lot_id.id if line.lot_id else False,
                    'company_id': self.warehouse_id.company_id.id or self.env.company.id,
                    'picked': True,
                })

        picking.with_context(cancel_backorder=True, skip_backorder=True).button_validate()
        self.write({'is_received': True, 'status': 'received'})

        # Auto-route single-material batch if sorting default exists
        active_lines = self.line_ids.filtered(lambda l: l.quantity > 0)
        if active_lines and not self.category_id and self.batch_type != 'collection':
            unique_materials = list(set(active_lines.mapped('material_id').ids))
            if len(active_lines) == 1 or len(unique_materials) == 1:
                sort_based_on = self.env['ir.config_parameter'].sudo().get_param(
                    'wm_collection.wm_sort_based_on', default='material'
                )
                if sort_based_on == 'material':
                    materials = active_lines.mapped('material_id')
                    if materials:
                        material = materials[0]
                        config = self.env['wm.waste.material.sort.config'].search([
                            ('material_id', '=', material.id)
                        ], limit=1)
                        if config and config.dest_location_id:
                            if self.location_id != config.dest_location_id:
                                self._do_internal_move(
                                    self.line_ids[0].product_id,
                                    self.quantity,
                                    self.location_id,
                                    config.dest_location_id,
                                    self.lot_id,
                                    origin=_('Auto-Sort: %s') % self.name,
                                    uom=self.uom_id
                                )
                                self.location_id = config.dest_location_id
                    for line in active_lines:
                        line.sorted_qty = line.quantity
                    self.status = 'sorted'
                else:
                    for line in active_lines:
                        line.sorted_qty = line.quantity
                    self.status = 'sorting'

    def _check_sort_rights(self):
        """
        Verify that the current user has the 'Waste Manager' or 'Sorting
        Operator' security role before allowing sort operations, preventing
        unauthorised batch segregation.
        """
        if not (self.env.user.has_group('wm_base.group_wm_inventory_operator') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("Only Inventory & Yard Operators and Operations Managers can sort batches."))

    def _auto_sort_single_material(self):
        """
        Automatically create a single sorted child batch when the parent batch
        contains only one material type, skipping the manual sort wizard for
        operational efficiency.
        """
        self.ensure_one()
        active_lines = self.line_ids.filtered(lambda l: l.remaining_qty > 0)
        if not active_lines:
            raise UserError(_("There is nothing left to sort on this batch — all lines have already been fully sorted."))

        active_materials = active_lines.mapped('material_id')
        if len(active_materials) == 1 and not self.sorted_batch_ids:
            material = active_materials[0]
            config = self.env['wm.waste.material.sort.config'].search([
                ('material_id', '=', material.id)
            ], limit=1)

            if not config:
                raise UserError(_("This single-material batch cannot be automatically sorted because no default Sort Configuration exists for %s. Please create one first.") % material.name)

            if self.location_id != config.dest_location_id:
                self._do_internal_move(
                    self.line_ids[0].product_id, self.quantity, self.location_id, config.dest_location_id, self.lot_id,
                    origin=_('Auto-Sort: %s') % self.name, uom=self.uom_id
                )

            self.location_id = config.dest_location_id
            self.write({'status': 'sorted', 'sorting_status': 'sorted'})

            for line in self.line_ids:
                line.sorted_qty = line.quantity

            return config
        return False

    def action_sort_batch(self):
        """
        Open the waste batch sort wizard, pre-populated with the batch's
        material lines, enabling operators to allocate quantities into
        category-specific child batches.
        """
        self.ensure_one()
        self._check_sort_rights()
        if not self.is_received:
            raise UserError(_("Only received batches can be sorted."))

        active_lines = self.line_ids.filtered(lambda l: l.remaining_qty > 0)
        if not active_lines:
            raise UserError(_(
                "There is nothing left to sort on this batch — all lines "
                "have already been fully sorted."
            ))

        config = self._auto_sort_single_material()
        if config:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Auto-Sorted'),
                    'message': _('Single-material batch automatically sorted to %s.') % config.dest_location_id.display_name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }

        return {
            'name': _('Sort Batch'),
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch.sort.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_batch_id': self.id},
        }

    def action_sort_by_category(self):
        """
        Open the category-based sort wizard, grouping all batch material lines
        by their waste category and allowing operators to allocate quantities
        to category-specific child batches.
        """
        self.ensure_one()
        self._check_sort_rights()
        if not self.is_received:
            raise UserError(_("Only received batches can be sorted."))

        active_lines = self.line_ids.filtered(lambda l: l.remaining_qty > 0)
        if not active_lines:
            raise UserError(_(
                "There is nothing left to sort on this batch — all lines "
                "have already been fully sorted."
            ))

        return {
            'name': _('Sort by Category'),
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch.sort.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_batch_id': self.id, 'default_sort_by_category': True},
        }

    def action_sort_by_material(self):
        """
        Open the material-based sort wizard, presenting each distinct material
        product as an individual sort allocation line for fine-grained material
        stream separation.
        """
        self.ensure_one()
        self._check_sort_rights()
        if not self.is_received:
            raise UserError(_("Only received batches can be sorted."))

        active_lines = self.line_ids.filtered(lambda l: l.remaining_qty > 0)
        if not active_lines:
            raise UserError(_(
                "There is nothing left to sort on this batch — all lines "
                "have already been fully sorted."
            ))

        config = self._auto_sort_single_material()
        if config:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Auto-Sorted'),
                    'message': _('Single-material batch automatically sorted to %s.') % config.dest_location_id.display_name,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.client', 'tag': 'reload'},
                }
            }

        return {
            'name': _('Sort by Material'),
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch.sort.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_batch_id': self.id, 'default_sort_by_material': True},
        }

    def action_view_sorted_batches(self):
        """
        Open the list of child sorted batches derived from this parent batch,
        enabling supervisors to track sorting progress and review individual
        child batch states.
        """
        self.ensure_one()
        action = {
            'name': _('Sorted Into — %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'waste.batch',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.sorted_batch_ids.ids)],
            'context': {'create': False},
        }
        if len(self.sorted_batch_ids) == 1:
            action.update({'view_mode': 'form', 'res_id': self.sorted_batch_ids.id})
        return action

    def _do_internal_moves_batch(self, moves_data, origin=None):
        """
        Creates ONE stock.picking containing ONE stock.move per item in
        moves_data.         moves_data: list of dicts with keys: product, qty,
        src_loc, dest_loc, lot, uom
        """
        self.ensure_one()
        if not moves_data:
            return self.env['stock.picking']

        origin = origin or self.name
        company_id = self.warehouse_id.company_id.id or self.env.company.id
        first_src = moves_data[0]['src_loc']
        first_dest = moves_data[0]['dest_loc']

        picking_type = (
            self.warehouse_id.int_type_id
            or self.env['stock.picking.type'].search(
                [('warehouse_id', '=', self.warehouse_id.id),
                 ('code', '=', 'internal')], limit=1
            )
        )
        picking = self.env['stock.picking'].with_context(default_batch_id=False).create({
            'waste_batch_id': self.id,
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': first_src.id,
            'location_dest_id': first_dest.id,
            'origin': origin,
            'company_id': company_id,
        })

        move_records = []
        for item in moves_data:
            prod = item['product']
            qty = item['qty']
            src = item['src_loc']
            dest = item['dest_loc']
            uom = item.get('uom') or prod.uom_id
            lot = item.get('lot')

            if lot and lot.product_id != prod:
                matching_lot = self.env['stock.lot'].search([
                    ('product_id', '=', prod.id),
                    ('company_id', '=', company_id),
                    ('name', 'like', self.name)
                ], limit=1)
                lot = matching_lot if matching_lot else False

            move = self.env['stock.move'].create({
                'product_id': prod.id,
                'product_uom': uom.id,
                'product_uom_qty': qty,
                'location_id': src.id,
                'location_dest_id': dest.id,
                'picking_id': picking.id,
                'origin': origin,
                'company_id': company_id,
            })
            move_records.append((move, qty, uom, lot, src, dest))

        picking.action_confirm()
        picking.action_assign()

        for move, qty, uom, lot, src, dest in move_records:
            if move.move_line_ids:
                for ml in move.move_line_ids:
                    if lot:
                        ml.lot_id = lot.id
                    ml.quantity = uom._compute_quantity(qty, ml.product_uom_id) if (uom and ml.product_uom_id) else qty
                    ml.picked = True
            else:
                converted_qty = uom._compute_quantity(qty, move.product_uom) if (uom and move.product_uom) else qty
                self.env['stock.move.line'].create({
                    'move_id': move.id,
                    'product_id': move.product_id.id,
                    'product_uom_id': move.product_uom.id,
                    'quantity': converted_qty,
                    'location_id': src.id,
                    'location_dest_id': dest.id,
                    'lot_id': lot.id if lot else False,
                    'company_id': company_id,
                    'picked': True,
                })

        picking.with_context(cancel_backorder=True).button_validate()
        return picking

    def _do_internal_move(self, product, qty, src_loc, dest_loc,
                          lot=None, origin=None, uom=None):
        """
        Create and validate a stock internal transfer move to relocate
        recovered materials from the incoming waste location to the designated
        sorted-stock location.
        """
        return self._do_internal_moves_batch([{
            'product': product,
            'qty': qty,
            'src_loc': src_loc,
            'dest_loc': dest_loc,
            'lot': lot,
            'uom': uom,
        }], origin=origin)

    def _create_sorted_child_batch(self, lines_data, dest_location, mode='per_material'):
        """ Shared helper to create child batch(es) and execute batched stock picking moves. """
        self.ensure_one()
        self._check_sort_rights()
        total_sort_qty = sum(d['sort_qty'] for d in lines_data)
        if total_sort_qty <= 0:
            raise UserError(_("Sort quantity must be greater than zero."))

        with self.env.cr.savepoint():
            # Concurrency row-level lock on parent batch and lines
            self.env.cr.execute("SELECT id FROM waste_batch WHERE id = %s FOR UPDATE", [self.id])
            line_ids = [d['batch_line'].id for d in lines_data if d.get('batch_line')]
            if line_ids:
                self.env.cr.execute("SELECT id FROM waste_batch_line WHERE id IN %s FOR UPDATE", [tuple(line_ids)])
            self.invalidate_recordset(['line_ids'])

            for d in lines_data:
                line = d['batch_line']
                if d['sort_qty'] - line.remaining_qty > 1e-6:
                    raise UserError(_(
                        "Cannot sort %(qty)s of %(mat)s — only %(rem)s remains "
                        "unsorted on this line.",
                        qty=d['sort_qty'],
                        mat=line.material_id.display_name,
                        rem=line.remaining_qty,
                    ))

            production_loc = self.env.ref('stock.location_production', raise_if_not_found=False)
            if not production_loc:
                production_loc = self.env['stock.location'].search(
                    [('usage', '=', 'production')], limit=1
                )
            if not production_loc:
                raise UserError(_(
                    "No production location found. Please configure a stock "
                    "location with usage 'Production' to use as the sorting "
                    "bridge location."
                ))

        # Batch 1: Move all source products from self.location_id -> production_loc in ONE picking
        source_moves = []
        for d in lines_data:
            batch_line = d['batch_line']
            sort_qty = d['sort_qty']
            source_product = batch_line.product_id or self.line_ids[0].product_id
            source_lot = batch_line.lot_id or self.lot_id
            source_moves.append({
                'product': source_product,
                'qty': sort_qty,
                'src_loc': self.location_id,
                'dest_loc': production_loc,
                'lot': source_lot,
                'uom': batch_line.uom_id or self.uom_id,
            })
        self._do_internal_moves_batch(source_moves, origin=self.name)

        child_batches = self.env['waste.batch']

        if mode == 'consolidated':
            child_line_vals = []
            for d in lines_data:
                batch_line = d['batch_line']
                sort_qty = d['sort_qty']
                product = d.get('dest_product') or batch_line.product_id
                child_line_vals.append((0, 0, {
                    'product_id': product.id,
                    'material_id': batch_line.material_id.id,
                    'quantity': sort_qty,
                    'sorted_qty': 0.0,
                    'uom_id': batch_line.uom_id.id or self.uom_id.id,
                    'net_weight': sort_qty if (batch_line.uom_id.id or self.uom_id.id) == self.env.ref(
                        'uom.product_uom_kgm', raise_if_not_found=False).id else 0.0,
                    'notes': _('Split from %(batch)s, line: %(material)s') % {
                        'batch': self.name, 'material': batch_line.material_id.display_name,
                    },
                }))

            child_batch = self.env['waste.batch'].create({
                'draft_quantity': total_sort_qty,
                'uom_id': self.uom_id.id,
                'warehouse_id': self.warehouse_id.id,
                'location_id': dest_location.id,
                'received_date': fields.Date.today(),
                'parent_batch_id': self.id,
                'is_category_batch': True,
                'batch_type': 'sorted_material',
                'sorting_status': 'sorted',
                'category_id': self.category_id.id if self.category_id else (lines_data[0]['batch_line'].category_id.id if lines_data else False),
                'line_ids': child_line_vals,
            })
            child_batch.with_context(skip_inspection_check=True).action_receive_batch()
            child_batches |= child_batch

            dest_moves = []
            for child_line, d in zip(child_batch.line_ids, lines_data):
                dest_loc = d.get('dest_location') or dest_location
                dest_moves.append({
                    'product': child_line.product_id,
                    'qty': child_line.quantity,
                    'src_loc': production_loc,
                    'dest_loc': dest_loc,
                    'lot': child_line.lot_id or child_batch.lot_id,
                    'uom': child_line.uom_id or child_batch.uom_id,
                })
            self._do_internal_moves_batch(dest_moves, origin=child_batch.name)
            child_batch.write({'is_received': True, 'status': 'received'})

        else:  # per_material mode
            dest_moves = []
            created_data_list = []
            for d in lines_data:
                batch_line = d['batch_line']
                sort_qty = d['sort_qty']
                dest_product = d.get('dest_product') or batch_line.product_id
                dest_loc = d.get('dest_location') or dest_location

                child_batch = self.env['waste.batch'].create({
                    'draft_quantity': sort_qty,
                    'uom_id': batch_line.uom_id.id or self.uom_id.id,
                    'warehouse_id': self.warehouse_id.id,
                    'location_id': dest_loc.id,
                    'received_date': fields.Date.today(),
                    'parent_batch_id': self.id,
                    'is_material_batch': True,
                    'batch_type': 'sorted_material',
                    'sorting_status': 'sorted',
                    'category_id': batch_line.category_id.id or self.category_id.id,
                    'line_ids': [(0, 0, {
                        'product_id': dest_product.id,
                        'material_id': batch_line.material_id.id,
                        'quantity': sort_qty,
                        'sorted_qty': 0.0,
                        'uom_id': batch_line.uom_id.id or self.uom_id.id,
                        'net_weight': sort_qty if (batch_line.uom_id.id or self.uom_id.id) == self.env.ref(
                            'uom.product_uom_kgm', raise_if_not_found=False).id else 0.0,
                        'notes': _('Split from %(batch)s, line: %(material)s') % {
                            'batch': self.name, 'material': batch_line.material_id.display_name,
                        },
                    })],
                })
                child_batch.with_context(skip_inspection_check=True).action_receive_batch()
                child_batches |= child_batch

                dest_moves.append({
                    'product': dest_product,
                    'qty': sort_qty,
                    'src_loc': production_loc,
                    'dest_loc': dest_loc,
                    'lot': child_batch.line_ids[0].lot_id or child_batch.lot_id,
                    'uom': child_batch.uom_id,
                })
                created_data_list.append((child_batch, batch_line, sort_qty, dest_loc))

            # Batch 2: Move all destination products from production_loc -> dest_loc in ONE picking
            self._do_internal_moves_batch(dest_moves, origin=self.name)
            for child_batch, _bl, _sq, _dl in created_data_list:
                child_batch.write({'is_received': True, 'status': 'received'})

        for d in lines_data:
            d['batch_line'].sorted_qty += d['sort_qty']

        materials_str = ", ".join(d['batch_line'].material_id.display_name for d in lines_data)
        self.message_post(body=_(
            "Sorted %(qty)s %(uom)s of %(materials)s out to batch(es) %(child)s (%(loc)s).",
            qty=total_sort_qty,
            uom=self.uom_id.name,
            materials=materials_str,
            child=", ".join(child_batches.mapped('name')),
            loc=dest_location.complete_name,
        ))
        for child_batch in child_batches:
            child_batch.message_post(body=_(
                "Created by sorting %(qty)s %(uom)s out of batch %(parent)s.",
                qty=child_batch.draft_quantity,
                uom=child_batch.uom_id.name,
                parent=self.name,
            ))

        if self.line_ids.filtered(lambda l: l.remaining_qty > 1e-6):
            self.write({'status': 'sorting', 'sorting_status': 'in_sorting'})
        else:
            self.write({'status': 'sorted', 'sorting_status': 'sorted'})

        return child_batches

    def _execute_sort_move(self, batch_line, sort_qty, dest_product, dest_location):
        """
        Execute a single material sort operation by creating the child batch
        record and its corresponding internal stock move for the specified
        quantity and category.
        """
        self.ensure_one()
        lines_data = [{
            'batch_line': batch_line,
            'sort_qty': sort_qty,
            'dest_product': dest_product,
            'dest_location': dest_location,
        }]
        child_batches = self._create_sorted_child_batch(lines_data, dest_location, mode='per_material')
        return child_batches[0]

    def _execute_grouped_sort_moves(self, lines_data, dest_location, dest_product=None):
        """
        Process multiple material sort lines in a single batch operation,
        creating all child batches and stock moves atomically to ensure data
        consistency.
        """
        self.ensure_one()
        child_batches = self._create_sorted_child_batch(lines_data, dest_location, mode='consolidated')
        return child_batches[0]

    def action_dispose_batch(self):
        """ Mark waste batch as disposed and clear stock quants to scrap location. """
        for batch in self:
            if not (self.env.user.has_group('wm_base.group_wm_inventory_operator') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
                raise UserError(_("Only Inventory & Yard Operators and Operations Managers can dispose of waste batches."))

            with self.env.cr.savepoint():
                self.env.cr.execute("SELECT id, status FROM waste_batch WHERE id = %s FOR UPDATE", [batch.id])
                locked_row = self.env.cr.fetchone()
                if not locked_row or locked_row[1] in ('recycled', 'sold', 'disposed') or batch.status in ('recycled', 'sold', 'disposed'):
                    raise UserError(_("Completed or already disposed batches cannot be disposed again."))

                active_lines = batch.line_ids.filtered(lambda l: l.quantity > 0)
                if batch.sorted_batch_ids and active_lines and all(l.remaining_qty <= 0 for l in active_lines):
                    child_names = ', '.join(batch.sorted_batch_ids.mapped('name'))
                    raise UserError(_(
                        "Cannot dispose Waste Batch '%(name)s': This batch has been fully sorted into child batches (%(children)s). "
                        "Please dispose the child batches individually instead.",
                        name=batch.name,
                        children=child_names,
                    ))

                # If received into stock, move physical quantities to scrap/loss location
                if batch.is_received and batch.location_id:
                    scrap_loc = self.env.ref('stock.stock_location_scrapped', raise_if_not_found=False)
                    if not scrap_loc:
                        scrap_loc = self.env['stock.location'].search([
                            ('usage', '=', 'inventory'),
                            ('company_id', 'in', [batch.warehouse_id.company_id.id, False])
                        ], limit=1)

                    if scrap_loc:
                        for line in batch.line_ids.filtered(lambda l: l.quantity > 0 and l.product_id):
                            qty_to_scrap = line.remaining_qty if line.sorted_qty else line.quantity
                            if qty_to_scrap > 0:
                                batch._do_internal_move(
                                    product=line.product_id,
                                    qty=qty_to_scrap,
                                    src_loc=batch.location_id,
                                    dest_loc=scrap_loc,
                                    lot=line.lot_id or batch.lot_id,
                                    origin=_('Disposal: %s') % batch.name,
                                    uom=line.uom_id or batch.uom_id,
                                )

                batch.write({'status': 'disposed'})

    def action_print_label(self):
        """
        Generate and open the printable batch label PDF containing barcode,
        batch reference, material category, weight, and handler information for
        physical labelling.
        """
        self.ensure_one()
        return self.env.ref('wm_collection.action_waste_batch_label').report_action(self)

    def action_start_inspection(self):
        """
        Launch the waste batch inspection workflow by creating a new inspection
        record pre-populated with batch details and transitioning the batch to
        'under inspection' state.
        """
        if not (self.env.user.has_group('wm_base.group_wm_inventory_operator') or self.env.user.has_group('wm_base.group_wm_ops_manager') or self.env.is_admin()):
            raise UserError(_("Only Inventory & Yard Operators and Operations Managers can start batch inspections."))
        inspection = self.env['wm.batch.inspection'].create({
            'batch_id': self.id,
            'state': 'in_progress',
        })
        self.write({
            'status':'inspection',
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Batch Inspection',
            'res_model': 'wm.batch.inspection',
            'view_mode': 'form',
            'res_id': inspection.id,
            'target': 'current',
        }
