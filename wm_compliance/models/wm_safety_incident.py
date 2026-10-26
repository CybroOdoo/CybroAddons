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
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class WmSafetyIncident(models.Model):
    """Safety and environmental incident tracking model for waste management operations."""
    _name = 'wm.safety.incident'
    _description = 'Safety Incident'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'wm.audit.mixin']
    _order = 'incident_datetime desc, id desc'

    name = fields.Char(
        string='Incident Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    incident_type = fields.Selection([
        ('near_miss', 'Near Miss'),
        ('injury', 'Injury'),
        ('vehicle_incident', 'Vehicle Incident'),
        ('spill', 'Spill'),
        ('property_damage', 'Property Damage'),
        ('other', 'Other'),
    ], string='Incident Type', required=True, default='near_miss', tracking=True)

    severity = fields.Selection([
        ('minor', 'Minor'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('fatality', 'Fatality'),
    ], string='Severity', required=True, default='minor', tracking=True)

    incident_datetime = fields.Datetime(
        string='Incident Date & Time',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver / Employee',
        tracking=True,
        help="Driver or personnel involved in the incident."
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        tracking=True,
        help="Vehicle involved in the incident if applicable."
    )
    route_id = fields.Many2one(
        'wm.route',
        string='Route',
        tracking=True,
        help="Route in progress when the incident occurred."
    )
    collection_point_id = fields.Many2one(
        'wm.collection.point',
        string='Collection Site',
        help="Customer site where the incident occurred if applicable."
    )
    location = fields.Char(
        string='Location / Address Description',
        help="Free-text location or specific details if not at a customer site."
    )
    description = fields.Text(
        string='Incident Description',
        required=True,
        help="Detailed explanation of how the incident occurred."
    )
    immediate_action_taken = fields.Text(
        string='Immediate Action Taken',
        help="Actions taken immediately after the incident to contain or resolve the situation."
    )
    is_osha_recordable = fields.Boolean(
        string='OSHA Recordable',
        tracking=True,
        help="Manually check if this incident meets OSHA recordability criteria (medical treatment beyond first aid, days away from work, restricted duty, loss of consciousness, or fatality)."
    )
    regulatory_report_required = fields.Boolean(
        string='Regulatory Report Required',
        tracking=True,
        help="Check if local/federal regulatory notification is required (e.g. EPA chemical spill thresholds)."
    )
    regulatory_deadline = fields.Date(
        string='Regulatory Reporting Deadline',
        tracking=True,
    )
    incident_photo = fields.Image(
        string='Incident Photo',
        max_width=1920,
        max_height=1920,
        help="Photo evidence of the incident (e.g. vehicle damage, chemical spill, site condition)."
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('reported', 'Reported'),
        ('investigating', 'Investigating'),
        ('closed', 'Closed'),
    ], string='Status', default='draft', required=True, tracking=True, copy=False)

    @api.ondelete(at_uninstall=False)
    def _unlink_except_reported_incident(self):
        """Reported incidents are regulatory records: only drafts may be deleted."""
        for rec in self:
            if rec.state != 'draft' and not (self.env.su and self.env.context.get('bypass_compliance_lock')):
                raise UserError(_("Incident '%s' has been reported and cannot be deleted.") % rec.display_name)

    @api.constrains('regulatory_report_required', 'regulatory_deadline')
    def _check_regulatory_deadline(self):
        """Ensure regulatory_deadline is set when regulatory_report_required is checked."""
        for rec in self:
            if rec.regulatory_report_required and not rec.regulatory_deadline:
                raise ValidationError(_("A Regulatory Reporting Deadline is required when 'Regulatory Report Required' is checked on safety incident '%s'.") % rec.name)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence SI/00001 for safety incidents."""
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('wm.safety.incident') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Prevent modifying closed safety incidents unless resetting state."""
        for rec in self:
            if rec.state == 'closed' and any(k != 'state' for k in vals.keys()):
                raise UserError(_("Cannot modify a closed safety incident ('%s'). Reset it to draft first to make changes.") % rec.name)
        return super().write(vals)

    def action_report(self):
        """Transition incident from draft to reported state (atomic multi-record validation)."""
        invalid = self.filtered(lambda r: r.state != 'draft')
        if invalid:
            names = ", ".join(invalid.mapped('name'))
            raise UserError(_("Only draft safety incidents can be reported. The following record(s) cannot be reported: %s") % names)
        self.write({'state': 'reported'})
        for rec in self:
            rec.message_post(body=_("Safety Incident reported."))

    def action_investigate(self):
        """Transition incident to investigating state (atomic multi-record validation)."""
        invalid = self.filtered(lambda r: r.state not in ('draft', 'reported'))
        if invalid:
            names = ", ".join(invalid.mapped('name'))
            raise UserError(_("The following record(s) cannot be set to investigating: %s") % names)
        self.write({'state': 'investigating'})
        for rec in self:
            rec.message_post(body=_("Safety Incident investigation initiated."))

    def action_close(self):
        """Close safety incident after investigation is complete (atomic multi-record validation)."""
        invalid = self.filtered(lambda r: r.state not in ('reported', 'investigating'))
        if invalid:
            names = ", ".join(invalid.mapped('name'))
            raise UserError(_("Only reported or investigating safety incidents can be closed. The following record(s) cannot be closed: %s") % names)
        self.write({'state': 'closed'})
        for rec in self:
            rec.message_post(body=_("Safety Incident closed."))

    def action_reset_to_draft(self):
        """Reset safety incident back to draft state (atomic multi-record validation)."""
        self.write({'state': 'draft'})
        for rec in self:
            rec.message_post(body=_("Safety Incident reset to draft."))
