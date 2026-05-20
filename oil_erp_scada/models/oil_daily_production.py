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

import logging

from odoo import api, fields, models
from odoo.orm.table_objects import Constraint
from odoo.tools.translate import _


_logger = logging.getLogger(__name__)


class OilDailyProduction(models.Model):
    """
    oil.daily.production  —  Daily Production Report
    Equivalent to SAP IS-Oil Production & Revenue Accounting (PRA) daily report.

    One record per well (project.task with is_oil_gas_well) per calendar day.
    Auto-created at midnight by a cron job that reads SCADA flow/volume tags
    for the past 24 hours and aggregates totals.

    Once a daily report has been populated by `create_from_scada`, an internal
    `_auto_process` runs:

      - if the lines contain storable products, an incoming stock.picking is
        created and validated, updating on-hand quantities;
      - if the report has a `lease_id` (copied from `scada.tag.lease_id`), every
        draft `oil.royalty` for that lease is appended with one line per
        production line; if no draft royalty exists for the lease, a new one is
        created.

    Both halves are idempotent: stock is skipped when `picking_id` is already
    set, royalties are skipped when `royalty_processed` is true.
    """
    _name = 'oil.daily.production'
    _description = 'Daily Production Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, well_id'
    _tag_date_unique = Constraint(
        'UNIQUE(tag_id, report_date, company_id)',
        'A daily production report already exists for this tag and date.'
    )


    # ── Identity ──────────────────────────────────────────────────────────
    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
    )
    report_date = fields.Date(
        string='Production Date',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    tag_id = fields.Many2one(
        'scada.tag',
        string='SCADA Tag',
        required=True,
        tracking=True,
    )
    well_id = fields.Many2one(
        'project.task',
        string='Well',
        domain=[('is_oil_gas_well', '=', True)],
        tracking=True,
    )
    lease_id = fields.Many2one(
        'oil.lease.agreement',
        string='Lease Agreement',
        tracking=True,
        help="Set automatically from the SCADA tag's lease. When present, "
             "royalty records are auto-updated for this lease."
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        related='well_id.project_id',
        store=True,
    )
    storage_location_id = fields.Many2one(
        'stock.location',
        string='Storage Location',
        domain=[('is_storage_tank', '=', True)],
        tracking=True,
        help='Storage location (with ATG enabled) where produced volumes '
             'are moved into stock. Auto-set from the project\'s storage '
             'location when applicable.',
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Inventory Move',
        readonly=True,
    )
    royalty_processed = fields.Boolean(
        string='Royalty Processed',
        default=False,
        readonly=True,
        copy=False,
        help='Internal flag — set once royalty lines have been generated '
             'for this report so re-runs of the cron do not duplicate them.',
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda s: s.env.company,
        required=True,
    )
    source = fields.Selection([
        ('scada', 'Auto — SCADA'),
        ('manual', 'Manual Entry'),
        ('mixed', 'SCADA + Manual Adjustment'),
    ], default='scada', string='Data Source')

    # ── Volumes ───────────────────────────────────────────────────────────
    line_ids = fields.One2many(
        'oil.daily.production.line', 'daily_production_id',
        string='Production Lines'
    )

    # ── Linked royalties (lease-scoped) ───────────────────────────────────
    lease_royalty_count = fields.Integer(
        string='Lease Royalty Count',
        compute='_compute_lease_royalty_count',
    )

    @api.depends('lease_id')
    def _compute_lease_royalty_count(self):
        Royalty = self.env['oil.royalty']
        for rec in self:
            rec.lease_royalty_count = Royalty.search_count([
                ('lease_id', '=', rec.lease_id.id),
            ]) if rec.lease_id else 0

    # ── ORM ───────────────────────────────────────────────────────────────
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = (
                        self.env['ir.sequence'].next_by_code('oil.daily.production')
                        or _('New')
                )
        return super().create(vals_list)

    # ── Tag → daily report defaults ───────────────────────────────────────
    @api.onchange('tag_id')
    def _onchange_tag_id(self):
        if self.tag_id:
            tag = self.tag_id
            well = tag.well_id
            if not well and tag.equipment_id and tag.equipment_id.well_site_ids:
                well = tag.equipment_id.well_site_ids[0]
            if well:
                self.well_id = well.id
            if tag.lease_id and not self.lease_id:
                self.lease_id = tag.lease_id.id
            # Auto-set storage location from project (only project-targeted
            # tags drive stock updates, so this is the only source).
            if (tag.odoo_model == 'project.project' and tag.project_id
                    and tag.project_id.storage_location_id
                    and not self.storage_location_id):
                self.storage_location_id = tag.project_id.storage_location_id.id

    # ── Auto processing entry point ───────────────────────────────────────
    def _auto_process(self):
        """Run royalty automation for this report.

        Stock updates are now driven per-reading by
        scada.tag._update_storage_stock_from_reading() — the daily report
        no longer touches inventory. Royalty creation stays here, gated on
        `lease_id` being set; idempotent via `royalty_processed`.
        """
        for rec in self:
            if rec.lease_id and not rec.royalty_processed and rec.line_ids:
                try:
                    rec._auto_update_royalties()
                    rec.royalty_processed = True
                except Exception:
                    _logger.exception(
                        'Auto royalty update failed for daily production %s',
                        rec.display_name,
                    )

    # ── Stock ─────────────────────────────────────────────────────────────
    def _auto_update_stock(self):
        """Create and validate an incoming stock.picking for storable lines.

        Lines whose product is not storable are silently skipped — on-hand
        quantity only exists for storable products. If no storable lines
        remain, the picking is not created.
        """
        self.ensure_one()
        if self.picking_id:
            return self.picking_id
        if not self.storage_location_id:
            _logger.info(
                'Daily production %s: no storage location, skipping stock update',
                self.display_name,
            )
            return False

        storable_lines = self.line_ids.filtered(
            lambda l: l.product_id.is_storable and l.produced_qty > 0
        )
        if not storable_lines:
            return False

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if not picking_type:
            _logger.warning(
                'No incoming picking type for company %s — skipping stock '
                'update on daily production %s',
                self.company_id.display_name, self.display_name,
            )
            return False

        source_location = self.env.ref('stock.stock_location_suppliers')

        move_vals = []
        for line in storable_lines:
            move_vals.append({
                'product_id': line.product_id.id,
                'product_uom_qty': line.produced_qty,
                'product_uom': line.uom_id.id,
                'location_id': source_location.id,
                'location_dest_id': self.storage_location_id.id,
            })

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': self.storage_location_id.id,
            'origin': _('Daily Production - %s', self.name),
            'scheduled_date': fields.Datetime.to_datetime(self.report_date),
            'move_ids': [(0, 0, vals) for vals in move_vals],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        result = picking.with_context(
            skip_backorder=True,
            skip_immediate=True,
        ).button_validate()
        if isinstance(result, dict) or picking.state != 'done':
            _logger.warning(
                'Stock picking %s for daily production %s did not validate '
                '(state=%s) — on-hand quantity not updated',
                picking.name, self.display_name, picking.state,
            )
            return False
        self.picking_id = picking.id
        return picking

    # ── Royalty ───────────────────────────────────────────────────────────
    def _auto_update_royalties(self):
        """Append production lines to every draft royalty on the lease.

        If no draft royalty exists for the lease, a new one is created.
        """
        self.ensure_one()
        if not self.lease_id or not self.line_ids:
            return self.env['oil.royalty']

        Royalty = self.env['oil.royalty']
        RoyaltyLine = self.env['oil.royalty.line']

        draft_royalties = Royalty.search([
            ('lease_id', '=', self.lease_id.id),
            ('state', '=', 'draft'),
        ])

        line_payload = self._royalty_line_vals()

        if draft_royalties:
            for royalty in draft_royalties:
                for vals in line_payload:
                    RoyaltyLine.create(dict(vals, royalty_id=royalty.id))
            return draft_royalties

        return Royalty.create({
            'name': _('Royalty for %s') % self.name,
            'lease_id': self.lease_id.id,
            'date': self.report_date,
            'royalty_type': 'percentage',
            'daily_production_id': self.id,
            'production_volume': sum(self.line_ids.mapped('produced_qty')),
            'company_id': self.company_id.id,
            'line_ids': [(0, 0, vals) for vals in line_payload],
        })

    def _royalty_line_vals(self):
        """Build oil.royalty.line value dicts from the production lines."""
        self.ensure_one()
        well_name = self.well_id.display_name or self.name
        vals = []
        for line in self.line_ids:
            vals.append({
                'product_id': line.product_id.id,
                'description': '[%s] %s' % (well_name, line.product_id.display_name),
                'date': self.report_date,
                'production_volume': line.produced_qty,
                'unit_price': line.product_id.lst_price,
            })
        return vals

    # ── SCADA cron entry points ───────────────────────────────────────────
    @api.model
    def create_from_scada(self, tag_id, report_date):
        from datetime import timedelta

        if not tag_id:
            return False

        day_start = fields.Datetime.to_datetime(
            fields.Date.to_string(report_date)
        )
        day_end = day_start + timedelta(days=1)

        tag = self.env['scada.tag'].browse(tag_id)

        existing = self.search([
            ('tag_id', '=', tag_id),
            ('report_date', '=', report_date),
            ('company_id', '=', self.env.company.id),
        ], limit=1)

        vals = {'source': 'scada'}

        if existing:
            new_rec = existing
            existing.write(vals)
        else:
            vals.update({
                'tag_id': tag_id,
                'report_date': report_date,
            })
            new_rec = self.create([vals])
            new_rec._onchange_tag_id()

        # Always sync lease from the tag—onchange only runs on first create
        if tag.lease_id and new_rec.lease_id != tag.lease_id:
            new_rec.lease_id = tag.lease_id.id

        # Auto-set storage location from project (only project-targeted
        # tags drive stock updates, so this is the only source).
        if not new_rec.storage_location_id:
            if (tag.odoo_model == 'project.project' and tag.project_id
                    and tag.project_id.storage_location_id):
                new_rec.storage_location_id = tag.project_id.storage_location_id.id

        reading_products = self.env['scada.reading.product'].search([
            ('reading_id.tag_id', '=', tag_id),
            ('reading_id.timestamp', '>=', day_start),
            ('reading_id.timestamp', '<', day_end),
            ('reading_id.quality', '=', 'good')
        ])

        product_totals = {}
        for rp in reading_products:
            pid = rp.product_id.id
            product_totals[pid] = product_totals.get(pid, 0.0) + rp.produced_qty

        # Only refresh lines if the report has not already been processed —
        # avoids losing the lines that downstream stock/royalty are based on.
        if not new_rec.picking_id and not new_rec.royalty_processed:
            new_rec.line_ids.unlink()
            line_vals = []
            for pid, total in product_totals.items():
                if total > 0:
                    prod = self.env['product.product'].browse(pid)
                    line_vals.append({
                        'product_id': prod.id,
                        'produced_qty': total,
                        'uom_id': prod.uom_id.id
                    })
            if line_vals:
                new_rec.write({'line_ids': [(0, 0, v) for v in line_vals]})

        new_rec._auto_process()
        return new_rec

    @api.model
    def auto_create_daily_production(self):
        from datetime import date, timedelta
        yesterday = date.today() - timedelta(days=1)

        tags = self.env['scada.tag'].search([
            ('is_production_tag', '=', True),
            ('active', '=', True),
        ])

        for tag in tags:
            self.create_from_scada(
                tag_id=tag.id,
                report_date=yesterday,
            )

    # ── Smart button ──────────────────────────────────────────────────────
    def action_view_lease_royalties(self):
        """Open all royalties for this report's lease."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Royalties'),
            'res_model': 'oil.royalty',
            'view_mode': 'list,form',
            'domain': [('lease_id', '=', self.lease_id.id)],
            'context': {'default_lease_id': self.lease_id.id},
        }


class OilDailyProductionLine(models.Model):
    _name = 'oil.daily.production.line'
    _description = 'Daily Production Line'

    daily_production_id = fields.Many2one(
        'oil.daily.production',
        string='Daily Production',
        ondelete='cascade',
        required=True,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
    )
    uom_id = fields.Many2one(
        'uom.uom',
        string='Unit of Measure',
        required=True,
        help="Select the unit of Measure."
    )
    produced_qty = fields.Float(
        string='Produced Qty',
        required=True,
        default=0.0,
    )
    rate = fields.Float(
        string='Rate',
        help='Production rate.',
    )

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Set the unit of measure from the selected product."""
        if self.product_id:
            self.uom_id = self.product_id.uom_id.id
