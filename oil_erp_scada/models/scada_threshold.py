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

from odoo import SUPERUSER_ID, fields, models
from odoo.tools.translate import _


class ScadaThreshold(models.Model):
    """
    Configurable alert rule tied to a SCADA tag.

    When process_reading() receives a value that satisfies the operator condition,
    this model auto-creates the configured action (HSE incident, maintenance request,
    or both) and records when it last fired.

    Cooldown: a threshold won't fire again until `cooldown_minutes` have passed
    since the last trigger — prevents alert floods.
    """
    _name = 'scada.threshold'
    _description = 'SCADA Alert Threshold'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'tag_id, severity desc'

    name = fields.Char(
        string='Rule Name',
        required=True,
        help='e.g. "Well-1 High Pressure Alarm"',
    )
    tag_id = fields.Many2one(
        'scada.tag',
        string='Tag',
        required=True,
        ondelete='cascade',
    )
    active = fields.Boolean(default=True)
    # ── Measurement filter (for Multi-Measurement Device tags) ─────────────
    # Leave as 'any' to fire on all measurements from this tag.
    # Set to a specific type (e.g. 'gas_ppm') so this rule fires ONLY when
    # that measurement type is received — even if the tag also sends pressure,
    # temperature, etc.
    applies_to = fields.Selection(
        [
            ('any',          'Any Measurement'),
            ('pressure',       'Pressure'),
            ('temperature',    'Temperature'),
            ('flow_rate',      'Flow Rate'),
            ('level',          'Level'),
            ('gas_ppm',        'Gas Concentration (ppm)'),
            ('vibration',      'Vibration'),
            ('valve_position', 'Valve Position'),
            ('cumulative',     'Cumulative Volume (meter)'),
            ('other',          'Other'),
        ],
        string='Applies to Measurement',
        default='any',
        help='Restrict this threshold to a specific measurement type. '
             'Essential for Multi-Measurement Device tags: e.g. set to '
             '"Gas Concentration" so a gas_ppm alarm does not fire when '
             'a pressure reading arrives on the same device tag.',
    )

    # ── Condition ──────────────────────────────────────────────────────────
    operator = fields.Selection(
        [
            ('>', 'Greater than  (>)'),
            ('>=', 'Greater or equal  (>=)'),
            ('<', 'Less than  (<)'),
            ('<=', 'Less or equal  (<=)'),
            ('==', 'Equal to  (==)'),
        ],
        string='Condition',
        required=True,
        default='>',
    )
    threshold_value = fields.Float(
        string='Threshold Value',
        required=True,
    )
    severity = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        string='Severity',
        required=True,
        default='medium',
        tracking=True,
    )

    # ── Action ─────────────────────────────────────────────────────────────
    action = fields.Selection(
        [
            ('hse_incident', 'Create HSE Incident'),
            ('maintenance', 'Create Maintenance Request'),
            ('both', 'Create HSE Incident + Maintenance Request'),
            ('log_only', 'Log Only (no record created)'),
        ],
        string='Action on Breach',
        required=True,
        default='hse_incident',
    )
    incident_type = fields.Selection(
        [
            ('accident', 'Accident'),
            ('near_miss', 'Near Miss'),
            ('dangerous_occurrence', 'Dangerous Occurrence'),
            ('environmental', 'Environmental'),
            ('property_damage', 'Property Damage'),
        ],
        string='Incident Type',
        default='dangerous_occurrence',
        help='Used when action creates an HSE incident.',
    )
    cooldown_minutes = fields.Integer(
        string='Cooldown (minutes)',
        default=30,
        help='Minimum minutes between consecutive triggers of this rule.',
    )
    send_sms = fields.Boolean(
        string='Send SMS on Trigger',
        help='When this rule fires, send an SMS to the followers of this '
             'threshold. The SMS is also logged in the chatter.',
    )

    # ── State ──────────────────────────────────────────────────────────────
    last_triggered = fields.Datetime(
        string='Last Triggered',
        readonly=True,
    )
    trigger_count = fields.Integer(
        string='Times Triggered',
        readonly=True,
        default=0,
    )

    # ── Core logic ─────────────────────────────────────────────────────────
    def evaluate(self, value, reading, measurement_type=None):
        """
        Called by ScadaTag.process_reading() for every active threshold on that tag.
        If the condition is met AND the cooldown has expired, fire the configured action.

        :param float value:            The incoming sensor value.
        :param scada.reading reading:  The newly created reading record.
        :param str measurement_type:   The effective measurement type of this reading.
                                       Used to skip thresholds that don't apply to
                                       this measurement (applies_to filter).
        """
        self.ensure_one()

        # Skip if this threshold is restricted to a specific measurement type
        # and the current reading is a different type.
        if self.applies_to and self.applies_to != 'any':
            if measurement_type != self.applies_to:
                return

        if not self._condition_met(value):
            return

        # Cooldown check
        if self.last_triggered:
            elapsed = (fields.Datetime.now() - self.last_triggered).total_seconds() / 60
            if elapsed < self.cooldown_minutes:
                return

        # Fire actions
        hse_id, maint_id = False, False
        if self.action in ('hse_incident', 'both'):
            hse_id = self._create_hse_incident(value, reading)
        if self.action in ('maintenance', 'both'):
            maint_id = self._create_maintenance_request(value, reading)

        # Optional SMS alert to followers
        if self.send_sms:
            self._send_threshold_sms(value, reading)

        # Update threshold state
        self.write({
            'last_triggered': fields.Datetime.now(),
            'trigger_count': self.trigger_count + 1,
        })

    def _send_threshold_sms(self, value, reading):
        """Log an SMS-style alert in the parent tag's chatter and dispatch SMS
        to the tag's followers.

        The threshold model has no form view, so the chatter message is posted
        on ``self.tag_id`` (which has a visible chatter). Followers of the tag
        receive an actual SMS via mail.thread._message_sms; if there are no
        followers the chatter entry is still recorded so the breach is auditable.
        """
        self.ensure_one()
        tag = self.tag_id
        if not tag:
            return
        body = _(
            "SCADA alert: rule '%(rule)s' triggered.\n"
            "Tag: %(tag)s\n"
            "Value: %(value)s (%(op)s %(threshold)s)\n"
            "Severity: %(severity)s",
            rule=self.name,
            tag=tag.tag_path or tag.display_name,
            value=value,
            op=self.operator,
            threshold=self.threshold_value,
            severity=dict(self._fields['severity'].selection).get(self.severity, self.severity),
        )
        partners = tag.sudo().message_partner_ids
        tag_sudo = tag.sudo()
        if partners:
            tag_sudo._message_sms(body=body, partner_ids=partners.ids)
        else:
            tag_sudo.message_post(
                body=body,
                message_type='comment',
                subtype_xmlid='mail.mt_note',
            )

    def _condition_met(self, value):
        """Check whether the given value satisfies this threshold operator and value."""
        ops = {
            '>': value > self.threshold_value,
            '>=': value >= self.threshold_value,
            '<': value < self.threshold_value,
            '<=': value <= self.threshold_value,
            '==': value == self.threshold_value,
        }
        return ops.get(self.operator, False)

    def _resolve_acting_user(self):
        """Pick a real user record for SCADA-driven record creation.

        SCADA pushes hit /api/scada/push with auth='none', so request.env.user
        can be empty and Odoo blows up with "Expected singleton: res.users()"
        the moment a default like reported_by=lambda self: self.env.user runs.
        Resolve a known-good user up front: prefer base.user_admin, fall back
        to the first internal user, then the SUPERUSER.
        """
        admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if admin:
            return admin
        internal = self.env['res.users'].sudo().search(
            [('share', '=', False), ('active', '=', True)], limit=1,
        )
        if internal:
            return internal
        return self.env['res.users'].sudo().browse(SUPERUSER_ID)

    def _create_hse_incident(self, value, reading):
        """Auto-create an HSE incident record when a threshold is breached."""
        tag = self.tag_id
        description = (
            f"Auto-generated by SCADA threshold rule: '{self.name}'\n"
            f"Tag: {tag.tag_path}\n"
            f"Value: {value}\n"
            f"Threshold: {self.operator} {self.threshold_value}\n"
            f"Equipment: {tag.equipment_id.name if tag.equipment_id else '—'}\n"
            f"Project: {tag.project_id.name if tag.project_id else '—'}\n"
            f"Storage Location: {tag.project_id.storage_location_id.display_name if tag.project_id and tag.project_id.storage_location_id else '—'}\n"
        )
        acting_user = self._resolve_acting_user()
        incident_vals = {
            'incident_type': self.incident_type,
            'severity': self.severity,
            'incident_date': fields.Datetime.now(),
            'immediate_action': description,
            'equipment_id': tag.equipment_id.id if tag.equipment_id else False,
            'project_id': tag.project_id.id if tag.project_id else False,
            'task_id': tag.well_id.id if tag.well_id else False,
            'company_id': tag.company_id.id,
            'reported_by': acting_user.id,
        }
        incident = self.env['oil.hse.incident'].with_user(acting_user.id).sudo().create(incident_vals)
        return incident.id

    def _create_maintenance_request(self, value, reading):
        """Auto-create a maintenance request when a threshold is breached."""
        tag = self.tag_id
        description = (
            f"Auto-created by SCADA: {tag.name} = {value} "
            f"({self.operator} {self.threshold_value})"
        )
        acting_user = self._resolve_acting_user()
        request = self.env['maintenance.request'].with_user(acting_user.id).sudo().create({
            'name': f'[SCADA] {tag.name} threshold breach — {self.name}',
            'equipment_id': tag.equipment_id.id if tag.equipment_id else False,
            'description': description,
            'maintenance_type': 'corrective',
            'company_id': tag.company_id.id,
        })
        return request.id
