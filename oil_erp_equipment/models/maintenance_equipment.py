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
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class MaintenanceEquipment(models.Model):
    """
    Extends 'maintenance.equipment' to include oil and gas specific attributes,
    such as criticality, operating parameters (pressure, temperature),
    and certification tracking.
    """
    _inherit = 'maintenance.equipment'

    is_oil_equipment = fields.Boolean(string='Oil & Gas Equipment',
                                      default=False,
                                      help="Enable this when oil & Gas "
                                           "Equipment applies.")

    # Oil & Gas Classification
    criticality = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
        ],
        string='Criticality',
        default='medium',
        tracking=True,
        help="Choose the criticality."
    )
    location_type = fields.Selection(
        [
            ('onshore', 'Onshore'),
            ('offshore', 'Offshore'),
        ],
        string='Location Type',
        help="Choose the location Type."
    )

    # Installation & Inspection
    installation_date = fields.Date(string='Installation Date',
                                    help="Select the date for installation Date.")
    last_inspection_date = fields.Date(string='Last Inspection Date',
                                       help="Select the date for last Inspection Date.")

    # Operating Parameters
    operating_pressure = fields.Float(
        string='Operating Pressure (PSI)',
        help="Normal operating pressure in PSI.",
    )
    operating_temperature = fields.Float(
        string='Operating Temperature (°F)',
        help="Normal operating temperature in Fahrenheit.",
    )
    max_capacity = fields.Float(
        string='Max Capacity',
        help="Maximum rated capacity (unit depends on equipment type).",
    )

    # Certification & Compliance
    certification_number = fields.Char(string='Certification Number',
                                       help="Enter the certification Number.")
    certification_expiry = fields.Date(string='Certification Expiry',
                                       help="Select the date for certification Expiry.")

    # Well / Site Reference
    well_site_ids = fields.Many2many(
        'project.task',
        'project_task_maintenance_equipment_rel',
        'equipment_id', 'task_id',
        string='Wells / Sites',
        domain="[('is_oil_gas_well', '=', True), ('project_id.is_oil_gas_project', '=', True)]",
        help='Oil and gas wells or sites where this equipment is deployed.',
    )

    @api.constrains('certification_expiry', 'installation_date')
    def _check_dates(self):
        """
        Validates that the certification expiry date is not before the installation date.
        """
        for rec in self:
            if rec.certification_expiry and rec.installation_date and rec.certification_expiry < rec.installation_date:
                raise ValidationError(
                    _("Certification expiry cannot be earlier than the installation date."))

    @api.constrains('operating_pressure', 'operating_temperature',
                    'max_capacity')
    def _check_operating_params(self):
        """
        Ensures that operating pressure and maximum capacity are not negative.
        """
        for rec in self:
            if rec.operating_pressure < 0:
                raise ValidationError(
                    _("Operating pressure cannot be negative."))
            if rec.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative."))

    def action_view_record(self):
        """
        Returns an action to view the equipment record in form view.
        """
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'maintenance.equipment',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }
