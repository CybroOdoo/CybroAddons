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
from odoo.exceptions import ValidationError


class WmSla(models.Model):
    """Reusable SLA tier (e.g. Standard, Premium) attachable to contracts with measurable commitments."""
    _name = 'wm.sla'
    _inherit = ['mail.thread']
    _description = 'Service Level Agreement'
    _order = 'name'

    name = fields.Char(string='Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    sla_line_ids = fields.One2many('wm.sla.line', 'sla_id', string='SLA Terms')
    breach_template_id = fields.Many2one(
        'mail.template', string='Breach Notification Template',
        domain="[('model', '=', 'wm.partner.contract')]",
        help="Only templates built for the Contract model can be used here, "
             "since the breach email is always sent against a specific contract.")
    description = fields.Text(string='Description')
    terms_and_conditions = fields.Html(string='Terms & Conditions', required=True)

    _name_uniq = models.Constraint('UNIQUE(name)', 'An SLA with this name already exists.')

    def action_open_send_email_wizard(self):
        """
        Open the SLA breach notification email wizard, pre-populating the
        recipient list from the SLA contract's designated compliance contacts.
        """
        self.ensure_one()
        return {
            'name': 'Send SLA Breach Email',
            'type': 'ir.actions.act_window',
            'res_model': 'wm.sla.send.email.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sla_id': self.id,
            }
        }


class WmSlaLine(models.Model):
    """One measurable SLA commitment line, e.g. 'Collection Frequency: 2× per week'."""
    _name = 'wm.sla.line'
    _description = 'SLA Commitment Line'
    _order = 'sequence, id'

    _SLA_TYPE_ALLOWED_UOM = {
        'collection_frequency': ('times_per_week', 'times_per_month'),
        'response_time': ('hours', 'days'),
        'resolution_time': ('hours', 'days'),
        'missed_pickup': ('hours', 'days'),
    }

    sequence = fields.Integer(default=10)
    sla_id = fields.Many2one('wm.sla', string='SLA', required=True, ondelete='cascade')
    sla_type = fields.Selection([
        ('response_time', 'Response Time'),
        ('resolution_time', 'Resolution Time'),
        ('collection_frequency', 'Collection Frequency'),
        ('missed_pickup', 'Missed Pickup Remedy'),
        ('other', 'Other'),
    ], string='Type', required=True, default='other')
    description = fields.Char(string='Commitment', required=True,
                               help="Human-readable statement of the commitment, "
                                    "e.g. 'Collect twice weekly'.")
    target_value = fields.Float(string='Target')
    uom = fields.Selection([
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('times_per_week', 'Times / Week'),
        ('times_per_month', 'Times / Month'),
    ], string='Unit')
    penalty_type = fields.Selection([
        ('none', 'None'),
        ('fixed_credit', 'Fixed Credit'),
        ('percentage_credit', 'Percentage Credit'),
        ('service_credit', 'Free Service Credit'),
    ], string='Penalty Type', default='none')
    penalty_value = fields.Float(
        string='Penalty Value',
        help="Amount (for Fixed Credit) or percentage (for Percentage Credit). "
             "Not used for None / Free Service Credit.")

    @api.constrains('sla_type', 'uom')
    def _check_uom_matches_sla_type(self):
        """
        Validate that the selected unit matches the allowable units for the
        chosen SLA type.
        """
        for rec in self:
            if not rec.uom:
                continue
            allowed = self._SLA_TYPE_ALLOWED_UOM.get(rec.sla_type)
            if allowed and rec.uom not in allowed:
                allowed_labels = [
                    label for value, label in dict(rec._fields['uom'].selection).items()
                    if value in allowed
                ]
                raise ValidationError(_(
                    "The unit '%(uom)s' is not valid for SLA type '%(sla_type)s'. "
                    "Allowed units: %(allowed)s.",
                    uom=dict(rec._fields['uom'].selection).get(rec.uom),
                    sla_type=dict(rec._fields['sla_type'].selection).get(rec.sla_type),
                    allowed=', '.join(allowed_labels),
                ))
