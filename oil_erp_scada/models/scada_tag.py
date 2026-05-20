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
from odoo.orm.table_objects import Constraint

from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ScadaTag(models.Model):
    """
    Master registry mapping every Ignition SCADA OPC-UA tag path to a
    specific Odoo model and record.

    1. A single Tag can record multiple measurements concurrently (e.g. Pressure + Temperature).
    2. Check the measure_* booleans to enable specific measurements for this device.
    """
    _name = 'scada.tag'
    _description = 'SCADA Tag Registry'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(string='Tag Name', required=True, tracking=True)
    tag_path = fields.Char(string='Ignition Tag Path', required=True, tracking=True,
                           help='Full OPC-UA / Ignition tag path, e.g. [default]Well1/Pressure/PSI')
    # ── Measurements (Toggles) ─────────────────────────────────────────────
    is_production_tag = fields.Boolean(
        string='Production Tag',
        help='If checked, this tag reports dynamic product quantities.'
    )
    product_ids = fields.Many2many(
        'product.product',
        string='Produced Products',
        help='Products that this tag can produce via SCADA keys.'
    )
    measure_pressure = fields.Boolean(string='Pressure')
    measure_temperature = fields.Boolean(string='Temperature')
    measure_flow_rate = fields.Boolean(string='Flow Rate')
    measure_level = fields.Boolean(string='Level')
    measure_gas_ppm = fields.Boolean(string='Gas Concentration (ppm)')
    measure_vibration = fields.Boolean(string='Vibration')
    measure_valve_position = fields.Boolean(string='Valve Position')
    measure_cumulative = fields.Boolean(string='Cumulative Volume (meter)')
    measure_other = fields.Boolean(string='Other')

    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company, required=True)

    # ── Target model ───────────────────────────────────────────────────────
    odoo_model = fields.Selection([
        ('maintenance.equipment', 'Equipment'),
        ('project.project', 'Project'),
        ('delivery.carrier', 'Pipeline'),
        ('none', 'Log Only'),
    ], string='Target Odoo Model', default='maintenance.equipment', required=True)

    equipment_id = fields.Many2one('maintenance.equipment', string='Equipment',
                                   domain=[('is_oil_equipment', '=', True)], tracking=True)

    project_id = fields.Many2one('project.project', string='Project', tracking=True,
                                 domain=[('is_oil_gas_project', '=', True)],
                                 context={'default_is_oil_gas_project': True})
    well_id = fields.Many2one('project.task', string='Well', domain="[('project_id', '=', project_id)]",
                              tracking=True)
    carrier_id = fields.Many2one('delivery.carrier', string='Pipeline Method', tracking=True)
    lease_id = fields.Many2one(
        'oil.lease.agreement',
        string='Lease Agreement',
        tracking=True,
        help='Lease agreement assigned to daily production reports created '
             'from this tag. When set, royalties are auto-updated alongside '
             'stock when the cron creates a daily report.',
    )

    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        tracking=True,
        help='Link this tag to a Work Center for machine state, output count, or energy tracking.',
    )
    workcenter_tag_role = fields.Selection([
        ('state', 'Machine State (integer 0-4)'),
        ('output', 'Production Output / Count'),
        ('energy', 'Energy Meter (kWh)'),
        ('temperature', 'Temperature'),
        ('pressure', 'Pressure'),
        ('other', 'Other / Log Only'),
    ], string='Work Center Role', default='other',
        help='How this tag feeds the linked Work Center.',
    )

    # ── Live state ─────────────────────────────────────────────────────────
    last_quality = fields.Selection([('good', 'Good'), ('bad', 'Bad'), ('uncertain', 'Uncertain')],
                                    string='Last Quality', readonly=True, default='good')
    last_sync = fields.Datetime(string='Last Sync', readonly=True)
    previous_value = fields.Float(string='Previous Value', readonly=True,
                                  help='Used to compute delta for cumulative tags.')

    reading_ids = fields.One2many('scada.reading', 'tag_id', string='Readings History')
    production_log_ids = fields.One2many('scada.reading.product', 'tag_id', string='Production Logs')
    reading_count = fields.Integer(compute='_compute_reading_count', string='Readings')
    threshold_ids = fields.One2many('scada.threshold', 'tag_id', string='Alert Thresholds')

    # ── Retention Policy ──────────────────────────────────────────────────
    has_retention = fields.Boolean(
        string='Enable Retention Policy',
        default=False,
        help='If checked, readings older than the specified period will be automatically deleted.',
        tracking=True,
    )
    retention_period = fields.Integer(
        string='Retention Period',
        default=30,
        help='How many days/weeks/months/years to keep readings.',
        tracking=True,
    )
    retention_unit = fields.Selection([
        ('days', 'Days'),
        ('weeks', 'Weeks'),
        ('months', 'Months'),
        ('years', 'Years'),
    ], string='Retention Unit', default='days', tracking=True)

    _tag_path_company_unique = Constraint(
        'UNIQUE(tag_path, company_id)',
        'Tag path must be unique per company.'
    )


    @api.depends('reading_ids')
    def _compute_reading_count(self):
        """Count the total readings recorded for this tag."""
        for rec in self:
            rec.reading_count = len(rec.reading_ids)

    @api.constrains('odoo_model', 'equipment_id', 'project_id', 'well_id', 'carrier_id')
    def _check_target_consistency(self):
        for rec in self:
            if rec.odoo_model == 'maintenance.equipment' and not rec.equipment_id:
                raise ValidationError(_('Link an Equipment record when target model is Equipment.'))

            if rec.odoo_model == 'project.project' and not rec.project_id:
                raise ValidationError(_('Link a Project record when target model is Project.'))

            if rec.odoo_model == 'delivery.carrier' and not rec.carrier_id:
                raise ValidationError(_('Link a Pipeline Method record when target model is Pipeline.'))

    # ─────────────────────────────────────────────────────────────────────
    # Core: process an incoming reading
    # ─────────────────────────────────────────────────────────────────────
    def action_simulate_reading(self):
        """Helper for users to test the full SCADA ↔ Odoo workflow from the UI."""
        self.ensure_one()
        return {
            'name': _('Simulate SCADA Reading'),
            'type': 'ir.actions.act_window',
            'res_model': 'scada.reading.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_tag_id': self.id, }
        }

    def process_reading(self, measurements, quality='good', timestamp=False, production_data=None):
        """
        Process incoming readings for this tag. Handles Multi-Measurement Devices.
        Central dispatch — called by the API controller.

        1. Logs the reading in scada.reading (wide format).
        """
        self.ensure_one()
        now = timestamp or fields.Datetime.now()

        # Capture the current previous_value before we process new ones
        prev = self.previous_value

        # 1. Log — create one wide record containing all measurements
        vals = {
            'tag_id': self.id,
            'quality': quality,
            'timestamp': now,
            'source': 'ignition',
        }

        has_data = False
        latest_val = False
        for mtype, val in measurements.items():
            # Check if this tag actually supports this measurement
            # (e.g. measure_pressure)
            toggle_field = f'measure_{mtype}'
            if hasattr(self, toggle_field) and getattr(self, toggle_field):
                field_name = f'val_{mtype}'
                if field_name in self.env['scada.reading']._fields:
                    vals[field_name] = val
                    has_data = True
                    latest_val = val

        if not has_data:
            return self.env['scada.reading']

        reading = self.env['scada.reading'].create(vals)

        # 3. Handle Production Data
        if self.is_production_tag and production_data:
            for scada_key, qty in production_data.items():
                product = self.product_ids.filtered(lambda p: p.scada_key == scada_key)
                if product:
                    self.env['scada.reading.product'].create({
                        'reading_id': reading.id,
                        'product_id': product[0].id,
                        'produced_qty': qty
                    })
            # Stock update is now driven per-reading (mirrors how
            # temperature flows into the storage location's live value).
            if quality == 'good' and reading.production_line_ids:
                self._update_storage_stock_from_reading(reading)

        # 4. Dispatch & 5. Threshold evaluation
        for mtype, val in measurements.items():
            toggle_field = f'measure_{mtype}'
            if not (hasattr(self, toggle_field) and getattr(self, toggle_field)):
                continue

            if quality == 'good':
                self._dispatch(val, prev, now, measurement_type=mtype)

            for threshold in self.threshold_ids.filtered('active'):
                threshold.evaluate(val, reading, measurement_type=mtype)

        # Update Live State with the newest value setting it as the new 'previous_value'
        if latest_val is not False:
            self.write({
                'previous_value': latest_val,
                'last_quality': quality,
                'last_sync': now
            })

        return reading

    def _dispatch(self, value, prev_value, timestamp, measurement_type=None):
        """
        Route the reading to its domain side-effects.

        Display-only "live_*" fields on equipment / workcenter / project are
        computed from scada.reading on read, so this method only triggers
        real domain operations (ATG level, machine state, output, energy).
        """
        self.ensure_one()
        mtype = measurement_type

        # ── Storage Location (ATG) routing ──────────────────────────────
        if self.odoo_model == 'project.project' and self.project_id:
            location = self.project_id.storage_location_id
            if location and location.is_storage_tank:
                if mtype == 'level':
                    location.receive_level(
                        level_mm=value,
                        timestamp=timestamp,
                    )
                elif mtype == 'temperature':
                    location.write({
                        'current_temperature_f': value,
                        'last_scada_sync': timestamp,
                    })

        # -- Work center routing ----------------------------------------
        if self.workcenter_id and self.workcenter_tag_role:
            role = self.workcenter_tag_role
            if role == 'state':
                self.workcenter_id.receive_machine_state(value, timestamp)
            elif role == 'output':
                self.workcenter_id.receive_output_count(value, timestamp)
            elif role == 'energy':
                self.workcenter_id.receive_energy(value, timestamp)

    # ─────────────────────────────────────────────────────────────────────
    # Per-reading stock update
    # ─────────────────────────────────────────────────────────────────────
    def _update_storage_stock_from_reading(self, reading):
        """Create and validate an incoming stock.picking from a single
        reading's production lines.

        Mirrors the way storage_location.current_temperature_f is updated
        on every temperature reading: every production reading drops its
        own quantities into the project's storage location.

        Conditions:
          - tag targets a project (odoo_model='project.project')
          - project has storage_location_id
          - reading has at least one storable production line with qty > 0
        """
        self.ensure_one()
        if self.odoo_model != 'project.project' or not self.project_id:
            return False
        location = self.project_id.storage_location_id
        if not location:
            return False

        # Mirror this reading's total produced qty onto the tank's
        # current_level_mm so the form shows "how much arrived in the
        # latest reading". Done for every production reading, even when
        # no line is storable (so a non-storable reading still updates
        # the live indicator).
        last_reading_qty = sum(reading.production_line_ids.mapped('produced_qty'))
        location.write({'current_level_mm': last_reading_qty})

        storable = reading.production_line_ids.filtered(
            lambda l: l.product_id.is_storable and l.produced_qty > 0
        )
        if not storable:
            return False

        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        if not picking_type:
            return False

        source_location = self.env.ref('stock.stock_location_suppliers')
        move_vals = [{
            'product_id': line.product_id.id,
            'product_uom_qty': line.produced_qty,
            'product_uom': line.product_id.uom_id.id,
            'location_id': source_location.id,
            'location_dest_id': location.id,
        } for line in storable]

        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': location.id,
            'origin': _('SCADA Reading #%s') % reading.id,
            'scheduled_date': reading.timestamp or fields.Datetime.now(),
            'move_ids': [(0, 0, vals) for vals in move_vals],
        })
        picking.action_confirm()
        picking.action_assign()
        for move in picking.move_ids:
            move.quantity = move.product_uom_qty
            move.picked = True
        picking.with_context(
            skip_backorder=True,
            skip_immediate=True,
        ).button_validate()
        return picking

    # ─────────────────────────────────────────────────────────────────────
    # Batch: process multiple values for one device at once
    # ─────────────────────────────────────────────────────────────────────
    @api.model
    def process_device_readings(self, device_type, device_id, values,
                                quality='good', timestamp=None):
        """
        Accept multiple tag values for a single device and process them
        in batch — one DB write per target record instead of one per tag.

        :param str device_type:  One of 'equipment', 'tank', 'meter',
                                 'workcenter', 'project', 'well'.
        :param int device_id:    Odoo record ID of the device.
        :param dict values:      Mapping of tag_type (or tag_path) → float value.
        :param str quality:      OPC-UA quality for all readings (default 'good').
        :param datetime timestamp: Timestamp for all readings (default now).
        :return: dict with processed/skipped counts and reading IDs.
        """
        now = timestamp or fields.Datetime.now()
        field_map = {
            'equipment': 'equipment_id',
            'workcenter': 'workcenter_id',
            'project': 'project_id',
            'well': 'well_id',
        }
        link_field = field_map.get(device_type)
        if not link_field:
            return {'status': 'error', 'message': f'Unknown device_type: {device_type}'}

        # Find all tags linked to this device
        domain = [(link_field, '=', device_id), ('active', '=', True)]
        device_tags = self.search(domain)
        if not device_tags:
            return {
                'status': 'error',
                'message': f'No active tags found for {device_type} id={device_id}',
            }

        # Build lookup: tag_type → tag record, tag_path → tag record
        by_type = {}
        by_path = {}
        for tag in device_tags:
            by_path[tag.tag_path] = tag
            # For tag_type lookup, keep first match per type (or accumulate)
            if hasattr(tag, 'tag_type') and tag.tag_type not in by_type:
                by_type[tag.tag_type] = tag

        processed = 0
        skipped = 0
        reading_ids = []
        errors = []

        # Resolve each key in values to a tag record
        matched_tags = []  # list of (tag, value)
        for key, val in values.items():
            tag = by_path.get(key) or by_type.get(key)
            if not tag:
                skipped += 1
                errors.append(f'No tag found for key "{key}" on {device_type} id={device_id}')
                continue
            matched_tags.append((tag, float(val)))

        # Batch-create all scada.reading records at once
        reading_vals_list = []
        for tag, val in matched_tags:
            reading_vals_list.append({
                'tag_id': tag.id,
                'value': val,
                'quality': quality,
                'timestamp': now,
                'source': 'ignition',
            })
        readings = self.env['scada.reading'].create(reading_vals_list) if reading_vals_list else self.env[
            'scada.reading']

        # Process each tag: update live state, dispatch, evaluate thresholds
        for idx, (tag, val) in enumerate(matched_tags):
            try:
                prev = tag.previous_value
                tag.write({
                    'previous_value': val,
                    'last_quality': quality,
                    'last_sync': now,
                })
                if quality == 'good':
                    tag._dispatch(val, prev, now)
                # Evaluate thresholds
                reading = readings[idx] if idx < len(readings) else False
                for threshold in tag.threshold_ids.filtered('active'):
                    if reading:
                        threshold.evaluate(val, reading)
                processed += 1
                reading_ids.append(readings[idx].id if idx < len(readings) else False)
            except Exception as e:
                skipped += 1
                errors.append(f'{tag.tag_path}: {e}')

        return {
            'status': 'ok',
            'processed': processed,
            'skipped': skipped,
            'reading_ids': reading_ids,
            'errors': errors,
        }

    # ── Retention Logic ───────────────────────────────────────────────────
    def action_purge_readings(self):
        """Manual trigger to purge old readings for this tag."""
        for rec in self:
            if rec.has_retention:
                rec._purge_readings()

    def _purge_readings(self):
        """Internal logic to delete old readings based on retention policy."""
        self.ensure_one()
        if not self.has_retention or self.retention_period <= 0:
            return 0

        kwargs = {self.retention_unit: self.retention_period}
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), **kwargs)

        old_readings = self.env['scada.reading'].search([
            ('tag_id', '=', self.id),
            ('timestamp', '<', cutoff)
        ])
        count = len(old_readings)
        if count > 0:
            old_readings.unlink()
        return count

    def action_view_storage_location(self):
        """
        Navigates to the linked project's storage location form view.
        """
        self.ensure_one()
        if self.odoo_model == 'project.project' and self.project_id:
            location = self.project_id.storage_location_id
            if location:
                return {
                    'type': 'ir.actions.act_window',
                    'name': _('Storage Location'),
                    'res_model': 'stock.location',
                    'res_id': location.id,
                    'view_mode': 'form',
                    'target': 'current',
                }
        return False

    @api.model
    def cron_purge_all_readings(self):
        """Daily cron job to purge readings for all tags with retention enabled."""
        tags = self.search([('has_retention', '=', True)])
        total_purged = 0
        for tag in tags:
            total_purged += tag._purge_readings()
        return total_purged
