# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Shalfa P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class VeterinaryAppointment(models.TransientModel):
    """Appointment Wizard for Veterinary Services."""
    _name = 'veterinary.appointment'
    _description = 'Appointment Wizard'

    service_type = fields.Selection([
        ('procedures', 'Procedures'),
        ('grooming', 'Grooming'),
        ('training', 'Training')
    ], string='Service Types',
        default="procedures",
        required=True,
        help="Type of service for the appointment")
    appointment_time = fields.Date(string='Time',
                                       required=True,
                                       help="Date of the appointment")
    doctor_id = fields.Many2one(
        string='Doctor',
        domain=[('staff', '=', 'doctor')],
        comodel_name="veterinary.employees",

        help="Doctor assigned to the appointment")
    patient = fields.Char(string="patient",
                          help="Name of the patient")

    @api.onchange('appointment_time')
    def _onchange_appointment_date(self):
        """Ensure the selected appointment date is not before the current date."""
        if self.appointment_time and self.appointment_time < fields.Datetime.today():
            raise ValidationError(_(
                "Selected appointment date cannot be before today's date."))

    def action_create_appointment(self):
        """Create the appointment based on the selected service type."""
        if self.service_type == 'procedures':
            return {
                self.env['case.appointments'].create({
                    'patient_id': self.patient,
                    'appointment_date': self.appointment_time,
                    'doctor_id': self.doctor_id.id,
                }),
            }
        elif self.service_type == 'grooming':
            return {
                self.env['animal.grooming'].create({
                    'patient_name_id': self.patient,
                    'appointment_date': self.appointment_time,
                }),
            }
        elif self.service_type == 'training':
            return {
                self.env['animal.training'].create({
                    'animal_id': self.patient,
                    'appointment_date': self.appointment_time,
                }),
            }
