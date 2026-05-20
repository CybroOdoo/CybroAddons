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


class MrpWorkCenterScada(models.Model):
    """
    mrp_workcenter_scada.py
    =======================
    Extends Odoo's mrp.workcenter with SCADA integration fields.

    Each Work Center = one physical machine on the shop floor.
    SCADA tags linked to a Work Center automatically:
      - Update live machine state (running / stopped / fault)
      - Start / pause / complete work orders based on machine state
      - Track OEE (Overall Equipment Effectiveness)
      - Log downtime with reason codes from PLC fault registers
      - Update qty_produced on the active work order from flow meters

    Machine State Tag (PLC integer register):
      0 = Idle
      1 = Running
      2 = Stopped / Paused
      3 = Fault / Alarm
      4 = Setup / Changeover
    """
    _inherit = 'mrp.workcenter'

    # ── SCADA tags linked to this work center ─────────────────────────────
    scada_tag_ids = fields.One2many(
        'scada.tag', 'workcenter_id',
        string='SCADA Tags',
        help='All sensor tags wired to this work center.',
    )
    scada_tag_count = fields.Integer(
        compute='_compute_scada_tag_count',
        string='SCADA Tags',
    )

    # ── Key tag references ────────────────────────────────────────────────
    state_tag_id = fields.Many2one(
        'scada.tag',
        string='Machine State Tag',
        domain=[('measure_other', '=', True)],
        help=(
            'PLC integer tag that reports machine state:\n'
            '0=Idle, 1=Running, 2=Stopped, 3=Fault, 4=Setup'
        ),
    )
    output_tag_id = fields.Many2one(
        'scada.tag',
        string='Output / Production Count Tag',
        domain=['|', '|', ('measure_flow_rate', '=', True), ('measure_cumulative', '=', True), ('measure_other', '=', True)],
        help='Tag that reports units produced or cumulative volume.',
    )
    energy_tag_id = fields.Many2one(
        'scada.tag',
        string='Energy Meter Tag (kWh)',
        domain=[('measure_other', '=', True)],
        help='Power meter tag — tracks energy consumption per work order.',
    )
    temperature_tag_id = fields.Many2one(
        'scada.tag',
        string='Temperature Tag',
        domain=[('measure_temperature', '=', True)],
    )
    pressure_tag_id = fields.Many2one(
        'scada.tag',
        string='Pressure Tag',
        domain=[('measure_pressure', '=', True)],
    )

    # ── Live state (written by SCADA) ─────────────────────────────────────
    live_machine_state = fields.Selection([
        ('idle',    'Idle'),
        ('running', 'Running'),
        ('stopped', 'Stopped'),
        ('fault',   'Fault / Alarm'),
        ('setup',   'Setup / Changeover'),
        ('unknown', 'Unknown'),
    ], string='Live Machine State', default='unknown', readonly=True,
        help='Current machine state pushed from SCADA in real time.')

    live_output_count = fields.Float(
        string='Live Output Count',
        readonly=True,
        digits=(16, 3),
        help='Current production count / volume from SCADA.',
    )
    live_energy_kwh = fields.Float(
        string='Live Energy (kWh)',
        readonly=True,
        digits=(16, 2),
    )
    live_temperature = fields.Float(
        string='Live Temperature',
        compute='_compute_live_temperature_pressure',
        digits=(10, 2),
        help='Latest temperature reading from the configured Temperature Tag.',
    )
    live_pressure = fields.Float(
        string='Live Pressure',
        compute='_compute_live_temperature_pressure',
        digits=(10, 2),
        help='Latest pressure reading from the configured Pressure Tag.',
    )
    last_scada_sync = fields.Datetime(
        string='Last SCADA Sync',
        readonly=True,
    )
    last_state_change = fields.Datetime(
        string='Last State Change',
        readonly=True,
        help='When the machine state last changed.',
    )

    # ── OEE tracking ──────────────────────────────────────────────────────
    oee_availability = fields.Float(
        string='Availability (%)',
        readonly=True,
        digits=(6, 2),
        help='Running time / Planned production time × 100.',
    )
    oee_performance = fields.Float(
        string='Performance (%)',
        readonly=True,
        digits=(6, 2),
        help='Actual output rate / Ideal output rate × 100.',
    )
    oee_quality = fields.Float(
        string='Quality (%)',
        readonly=True,
        digits=(6, 2),
        help='Good units / Total units × 100.',
    )
    oee_overall = fields.Float(
        string='OEE (%)',
        compute='_compute_oee_overall',
        store=True,
        digits=(6, 2),
    )

    # ── Downtime log ──────────────────────────────────────────────────────
    downtime_ids = fields.One2many(
        'mrp.workcenter.downtime',
        'workcenter_id',
        string='Downtime Log',
    )
    downtime_count = fields.Integer(
        compute='_compute_downtime_count',
        string='Downtimes',
    )

    # ── Auto work order control ───────────────────────────────────────────
    auto_start_workorder = fields.Boolean(
        string='Auto-start Work Order',
        default=False,
        help=(
            'When enabled and machine state changes to Running, '
            'Odoo automatically starts the next planned work order.'
        ),
    )
    auto_pause_workorder = fields.Boolean(
        string='Auto-pause Work Order',
        default=False,
        help='Pause active work order when machine stops.',
    )
    auto_log_downtime = fields.Boolean(
        string='Auto-log Downtime',
        default=True,
        help='Automatically create a downtime record when machine goes to Fault state.',
    )

    # ── Compute ───────────────────────────────────────────────────────────
    def _compute_scada_tag_count(self):
        for rec in self:
            rec.scada_tag_count = len(rec.scada_tag_ids)

    @api.depends('oee_availability', 'oee_performance', 'oee_quality')
    def _compute_oee_overall(self):
        """Calculate overall OEE as the product of availability, performance, and quality."""
        for rec in self:
            rec.oee_overall = (
                rec.oee_availability *
                rec.oee_performance *
                rec.oee_quality / 10000.0
            )

    @api.depends('downtime_ids')
    def _compute_downtime_count(self):
        for rec in self:
            rec.downtime_count = len(rec.downtime_ids)

    @api.depends('temperature_tag_id', 'pressure_tag_id')
    def _compute_live_temperature_pressure(self):
        Reading = self.env['scada.reading']
        for rec in self:
            rec.live_temperature = 0.0
            rec.live_pressure = 0.0
            if rec.temperature_tag_id:
                tr = Reading.search(
                    [('tag_id', '=', rec.temperature_tag_id.id)],
                    order='timestamp desc', limit=1,
                )
                rec.live_temperature = tr.val_temperature
            if rec.pressure_tag_id:
                pr = Reading.search(
                    [('tag_id', '=', rec.pressure_tag_id.id)],
                    order='timestamp desc', limit=1,
                )
                rec.live_pressure = pr.val_pressure

    # ── Core: receive machine state from SCADA ────────────────────────────
    def receive_machine_state(self, state_value, timestamp=None):
        """
        Called by scada_tag._dispatch() when the machine state tag changes.

        :param int state_value: PLC state register value
            0=Idle, 1=Running, 2=Stopped, 3=Fault, 4=Setup
        :param datetime timestamp: reading timestamp
        """
        self.ensure_one()
        now = timestamp or fields.Datetime.now()

        state_map = {
            0: 'idle',
            1: 'running',
            2: 'stopped',
            3: 'fault',
            4: 'setup',
        }
        new_state = state_map.get(int(state_value), 'unknown')
        prev_state = self.live_machine_state

        if new_state == prev_state:
            return  # No change — nothing to do

        self.write({
            'live_machine_state': new_state,
            'last_scada_sync': now,
            'last_state_change': now,
        })

        # Auto work order control
        if new_state == 'running' and self.auto_start_workorder:
            self._auto_start_workorder()
        elif new_state in ('stopped', 'idle') and self.auto_pause_workorder:
            self._auto_pause_workorder()
        elif new_state == 'fault':
            if self.auto_log_downtime:
                self._create_downtime_record(prev_state, now)
            if self.auto_pause_workorder:
                self._auto_pause_workorder()

    def receive_output_count(self, value, timestamp=None):
        """
        Called when the production count / flow meter tag updates.
        Updates the active work order's qty_produced.
        """
        self.ensure_one()
        self.write({
            'live_output_count': value,
            'last_scada_sync': timestamp or fields.Datetime.now(),
        })
        # Update active work order qty_produced
        active_wo = self._get_active_workorder()
        if active_wo:
            active_wo.write({'qty_production': value})

    def receive_energy(self, kwh, timestamp=None):
        """Update energy consumption from SCADA power meter."""
        self.ensure_one()
        self.write({
            'live_energy_kwh': kwh,
            'last_scada_sync': timestamp or fields.Datetime.now(),
        })

    # ── Work order auto-control ───────────────────────────────────────────
    def _get_active_workorder(self):
        """Return the currently active (in-progress) work order for this WC."""
        return self.env['mrp.workorder'].search([
            ('workcenter_id', '=', self.id),
            ('state', '=', 'progress'),
        ], limit=1)

    def _get_next_planned_workorder(self):
        """Return the next ready work order for this WC."""
        return self.env['mrp.workorder'].search([
            ('workcenter_id', '=', self.id),
            ('state', '=', 'ready'),
        ], order='date_planned_start asc', limit=1)

    def _auto_start_workorder(self):
        """Start the next planned work order when machine starts running."""
        wo = self._get_next_planned_workorder()
        if wo:
            wo.button_start()
            wo.production_id.message_post(
                body=_('Work order auto-started by SCADA — machine state: Running.')
            )

    def _auto_pause_workorder(self):
        """Pause active work order when machine stops."""
        wo = self._get_active_workorder()
        if wo:
            wo.button_pending()
            wo.production_id.message_post(
                body=_('Work order auto-paused by SCADA — machine state: %s.')
                % self.live_machine_state
            )

    def _create_downtime_record(self, previous_state, timestamp):
        """Create a downtime log entry when machine goes to Fault."""
        self.ensure_one()
        self.env['mrp.workcenter.downtime'].create({
            'workcenter_id': self.id,
            'start_time': timestamp,
            'reason': _(
                'Auto-logged by SCADA. Machine changed from "%s" to "fault".'
            ) % previous_state,
            'state': 'open',
        })

    # ── Actions ───────────────────────────────────────────────────────────
    def action_view_scada_tags(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'SCADA Tags — {self.name}',
            'res_model': 'scada.tag',
            'view_mode': 'list,form',
            'domain': [('workcenter_id', '=', self.id)],
            'context': {'default_workcenter_id': self.id},
        }

    def action_view_downtime(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Downtime Log — {self.name}',
            'res_model': 'mrp.workcenter.downtime',
            'view_mode': 'list,form',
            'domain': [('workcenter_id', '=', self.id)],
        }


class MrpWorkCenterDowntime(models.Model):
    """
    Downtime log for a work center.
    Auto-created by SCADA when machine goes to Fault state.
    Can also be created manually.
    """
    _name = 'mrp.workcenter.downtime'
    _description = 'Work Center Downtime Log'
    _order = 'start_time desc'

    workcenter_id = fields.Many2one(
        'mrp.workcenter',
        string='Work Center',
        required=True,
        ondelete='cascade',
    )
    workorder_id = fields.Many2one(
        'mrp.workorder',
        string='Work Order',
        help='Work order that was interrupted by this downtime.',
    )
    start_time = fields.Datetime(
        string='Start Time',
        required=True,
        default=fields.Datetime.now,
    )
    end_time = fields.Datetime(string='End Time')
    duration_minutes = fields.Float(
        string='Duration (minutes)',
        compute='_compute_duration',
        store=True,
    )
    reason = fields.Text(string='Reason / Description')
    downtime_type = fields.Selection([
        ('mechanical',  'Mechanical Failure'),
        ('electrical',  'Electrical Failure'),
        ('process',     'Process Issue'),
        ('planned',     'Planned Maintenance'),
        ('changeover',  'Changeover / Setup'),
        ('scada_auto',  'Auto-logged by SCADA'),
        ('other',       'Other'),
    ], string='Downtime Type', default='scada_auto')
    state = fields.Selection([
        ('open',   'Open'),
        ('closed', 'Closed'),
    ], default='open', string='State')
    company_id = fields.Many2one(
        'res.company', default=lambda s: s.env.company
    )

    @api.depends('start_time', 'end_time')
    def _compute_duration(self):
        for rec in self:
            if rec.start_time and rec.end_time:
                delta = rec.end_time - rec.start_time
                rec.duration_minutes = delta.total_seconds() / 60.0
            else:
                rec.duration_minutes = 0.0

    def action_close(self):
        self.write({
            'end_time': fields.Datetime.now(),
            'state': 'closed',
        })
