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
from odoo.exceptions import ValidationError


class OilHseIncident(models.Model):
    """
    Model for recording and tracking Health, Safety, and Environment (HSE) incidents.
    Supports incident classification, severity assessment, root cause analysis (RCA),
    and regulatory reporting status.
    """
    _name = 'oil.hse.incident'
    _description = 'HSE Incident & Near-Miss Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'incident_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        help='Auto-generated reference for the incident record.',
    )
    incident_date = fields.Datetime(
        string='Incident Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help='Date and time when the incident actually happened.',
    )
    report_date = fields.Date(
        string='Report Date',
        default=fields.Date.today,
        readonly=True,
        help='Date when the incident was formally reported in the system.',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        help='Company responsible for the incident record.',
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
        required=True,
        tracking=True,
        help='Classify the event so reporting and follow-up stay consistent.',
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
        tracking=True,
        help='Impact level of the incident.',
    )
    is_lti = fields.Boolean(
        string='Lost Time Injury',
        help='Enable this if the incident caused lost work days.',
    )
    lti_days = fields.Integer(
        string='Lost Days',
        help='Number of work days lost because of the incident.',
    )
    is_fatality = fields.Boolean(
        string='Fatality',
        help='Enable this if the incident resulted in a death.',
    )
    is_regulatory_reportable = fields.Boolean(
        string='Regulatory Reportable',
        compute='_compute_regulatory_reportable',
        store=True,
        help='Checked automatically for fatal or critical incidents.',
    )

    task_id = fields.Many2one(
        'project.task',
        string='Well / Task',
        tracking=True,
        domain=[('project_id.is_oil_gas_project', '=', True)],
        help='Well, task, or field activity where the incident occurred.',
    )
    project_id = fields.Many2one(
        'project.project',
        string='Project',
        tracking=True,
        domain=[('is_oil_gas_project', '=', True)],
        help='Project where the incident occurred.',
    )
    location_description = fields.Char(
        string='Exact Location / GPS',
        help='Enter a precise physical location, landmark, or GPS reference.',
    )
    equipment_id = fields.Many2one(
        'maintenance.equipment',
        string='Equipment',
        domain=[('is_oil_equipment', '=', True)],
        help='Equipment involved in the incident, if any.',
    )

    reported_by = fields.Many2one(
        'res.users',
        string='Reported By',
        default=lambda self: self.env.user,
        required=True,
        help='User who is submitting the incident report.',
    )
    injured_party_id = fields.Many2one(
        'res.partner',
        string='Injured Party',
        help='Person affected by the incident, if applicable.',
    )
    injured_party_type = fields.Selection(
        [
            ('employee', 'Employee'),
            ('contractor', 'Contractor'),
            ('visitor', 'Visitor'),
        ],
        string='Injured Party Type',
        help='Relationship of the injured person to the operation.',
    )
    witness_ids = fields.Many2many(
        'res.partner',
        string='Witnesses',
        help='People who witnessed the event or can support the investigation.',
    )

    root_cause = fields.Selection(
        [
            ('human_error', 'Human Error'),
            ('equipment_failure', 'Equipment Failure'),
            ('procedure_gap', 'Procedure Gap'),
            ('environmental', 'Environmental'),
            ('unknown', 'Unknown'),
        ],
        string='Root Cause',
        help='Primary root cause identified during the investigation.',
    )
    root_cause_detail = fields.Text(
        string='Root Cause Detail',
        help='Detailed explanation of how the root cause was determined.',
    )
    immediate_action = fields.Text(
        string='Immediate Corrective Action',
        help='Immediate containment or corrective steps taken after the incident.',
    )
    rca_ids = fields.One2many(
        'oil.hse.incident.rca',
        'incident_id',
        string='Corrective Actions',
        help='Follow-up actions required to prevent recurrence.',
    )
    investigation_by = fields.Many2one(
        'res.users',
        string='Investigation By',
        help='User assigned to lead the investigation.',
    )
    investigation_deadline = fields.Date(
        string='Investigation Deadline',
        help='Target completion date for the investigation.',
    )

    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('reported', 'Reported'),
            ('under_investigation', 'Under Investigation'),
            ('closed', 'Closed'),
            ('regulatory_submitted', 'Regulatory Submitted'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        help='Current workflow stage of the incident.',
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Photos, reports, permits, and other supporting documents.',
    )

    @api.depends('severity', 'is_fatality')
    def _compute_regulatory_reportable(self):
        """
        Automatically marks incidents as regulatory reportable if they are fatal
        or have critical severity.
        """
        for rec in self:
            rec.is_regulatory_reportable = rec.severity == 'critical' or rec.is_fatality

    @api.onchange('is_lti')
    def _onchange_is_lti(self):
        """Clear lost days when the incident is not an LTI."""
        if not self.is_lti:
            self.lti_days = 0

    @api.onchange('is_fatality')
    def _onchange_is_fatality(self):
        """Default the severity to critical for fatal incidents."""
        if self.is_fatality and not self.severity:
            self.severity = 'critical'

    @api.constrains('incident_date', 'report_date')
    def _check_incident_dates(self):
        """
        Validates that the incident date is not in the future and that the
        report date is not before the incident date.
        """
        now = fields.Datetime.now()
        for rec in self:
            if rec.incident_date and rec.incident_date > now:
                raise ValidationError(
                    _('Incident date cannot be in the future.'))
            if rec.incident_date and rec.report_date and fields.Date.to_date(
                    rec.incident_date) > rec.report_date:
                raise ValidationError(
                    _('Report date cannot be earlier than the incident date.'))

    @api.constrains('is_lti', 'lti_days')
    def _check_lti_days(self):
        """Validate lost-time-injury days and related flags."""
        for rec in self:
            if rec.lti_days < 0:
                raise ValidationError(_('Lost days cannot be negative.'))
            if rec.is_lti and rec.lti_days <= 0:
                raise ValidationError(
                    _('Enter at least one lost day for a lost time injury.'))
            if not rec.is_lti and rec.lti_days:
                raise ValidationError(
                    _('Lost days must be zero unless the incident is marked as a lost time injury.'))

    @api.constrains('injured_party_id', 'injured_party_type')
    def _check_injured_party(self):
        """Keep injured party and party type values consistent."""
        for rec in self:
            if rec.injured_party_id and not rec.injured_party_type:
                raise ValidationError(
                    _('Select the injured party type when an injured party is specified.'))
            if rec.injured_party_type and not rec.injured_party_id:
                raise ValidationError(
                    _('Choose the injured party when an injured party type is set.'))

    @api.constrains('investigation_deadline', 'report_date')
    def _check_investigation_deadline(self):
        """Ensure the investigation deadline is not before the report date."""
        for rec in self:
            if rec.investigation_deadline and rec.report_date and rec.investigation_deadline < rec.report_date:
                raise ValidationError(
                    _('Investigation deadline cannot be earlier than the report date.'))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Assigns a unique reference number to new incident records.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'oil.hse.incident') or _('New')
        return super().create(vals_list)

    def action_report(self):
        """
        Moves the incident record to the 'Reported' state.
        Ensures required fields like type and severity are filled.
        """
        for rec in self:
            if not rec.incident_type or not rec.severity:
                raise ValidationError(
                    _('Incident type and severity are required before reporting the incident.'))
        self.write({'state': 'reported'})

    def action_investigate(self):
        """Move reported incidents into investigation."""
        for rec in self:
            if rec.state != 'reported':
                raise ValidationError(
                    _('Only reported incidents can move to investigation.'))
        self.write({'state': 'under_investigation'})

    def action_close(self):
        """Close incidents after a root cause is set."""
        for rec in self:
            if not rec.root_cause:
                raise ValidationError(
                    _('Set the root cause before closing the incident.'))
        self.write({'state': 'closed'})

    def action_submit_regulatory(self):
        """Mark reportable incidents as submitted to regulators."""
        for rec in self:
            if not rec.is_regulatory_reportable:
                raise ValidationError(
                    _('Only regulatory reportable incidents can be submitted to regulatory authorities.'))
        self.write({'state': 'regulatory_submitted'})

    def action_reset_draft(self):
        """Reset the incident back to draft."""
        self.write({'state': 'draft'})


class OilHseIncidentRca(models.Model):
    """
    Model for tracking specific corrective actions identified during
    the root cause analysis of an incident.
    """
    _name = 'oil.hse.incident.rca'
    _description = 'Incident Corrective Action'

    incident_id = fields.Many2one(
        'oil.hse.incident',
        string='Incident',
        required=True,
        ondelete='cascade',
        help='Incident linked to this corrective action.',
    )
    name = fields.Char(
        string='Action',
        required=True,
        help='Short description of the corrective action to complete.',
    )
    responsible_id = fields.Many2one(
        'res.users',
        string='Responsible',
        help='User responsible for completing the action.',
    )
    deadline = fields.Date(
        string='Deadline',
        help='Target date for closing this corrective action.',
    )
    state = fields.Selection(
        [
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
        ],
        string='Status',
        default='open',
        help='Current progress of the corrective action.',
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes, evidence, or closure remarks.',
    )

    @api.constrains('deadline', 'incident_id')
    def _check_deadline(self):
        """Ensure action deadlines do not predate the incident report."""
        for rec in self:
            if rec.deadline and rec.incident_id.report_date and rec.deadline < rec.incident_id.report_date:
                raise ValidationError(
                    _('Corrective action deadline cannot be earlier than the incident report date.')
                )
