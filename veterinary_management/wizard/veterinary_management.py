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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class VeterinaryManagement(models.TransientModel):
    """
    This model defines a wizard for generating veterinary management reports.
    The wizard allows users to select a service type (procedures, grooming, or training)
    and specify a date range for the report.
    """
    _name = 'veterinary.management'
    _description = 'Report Wizard'

    service_type = fields.Selection([
        ('procedures', 'Procedures'),
        ('grooming', 'Grooming'),
        ('training', 'Training')
    ], string='Service Types',
        default="procedures",
        required=True,
        help="Option to select which service type report you want to print in PDF report")

    start_date = fields.Date(string="Start Date",
                             help="Specify the start date for the report")
    end_date = fields.Date(string="End Date",
                           help="Specify the end date for the report")

    @api.constrains('start_date', 'end_date')
    def _check_to_date_from_date(self):
        """
        Constraint to validate that the start date is earlier than or equal to the end date.
        Raises:
            ValidationError: If the start date is later than the end date.
        """
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValidationError("From date must be less than to date")

    def action_pdf_report(self):
        """
        Function to generate a PDF report based on the selected service type
        and date range specified in the wizard.

        This method gathers data based on the selected `service_type` and applies
        date filters using `start_date` and `end_date`. It returns an action
        that opens the generated PDF report.

        Returns:
            dict: An action dictionary for displaying the PDF report.
        """
        data = []
        # Define a base domain for filtering records by date range
        domain = []

        if self.start_date and self.end_date:
            domain.append(('appointment_date', '>=', self.start_date))
            domain.append(('appointment_date', '<=', self.end_date))
        elif self.start_date:
            domain.append(('appointment_date', '>=', self.start_date))
        elif self.end_date:
            domain.append(('appointment_date', '<=', self.end_date))
        # Fetch and format records based on `service_type`
        if self.service_type == 'procedures':
            records = self.env['case.appointments'].search(domain)
            for record in records:
                data.append({
                    'case_number': record.case_no,
                    'patient_name': record.patient_id.name,
                    'doctor_name': record.doctor_id.name,
                    'appointment_date': record.appointment_date,
                    'treatment': record.treatment,
                    'is_admit': record.is_admit,
                    'vaccination': record.vaccination,
                    'status': record.state
                })
        elif self.service_type == 'grooming':
            records = self.env['animal.grooming'].search(domain)
            for record in records:
                data.append({
                    'case_number': record.grooming_no,
                    'patient_name': record.patient_name_id.name,
                    'doctor_name': record.grooming_employee_id.name,
                    'appointment_date': record.appointment_date,
                    'status': record.state
                })
        elif self.service_type == 'training':
            records = self.env['animal.training'].search(domain)
            for record in records:
                data.append({
                    'case_number': record.training_no,
                    'patient_name': record.animal_id.name,
                    'doctor_name': record.training_emp_id.name,
                    'appointment_date': record.appointment_date,
                    'animal_type': record.animal_type_id.name,
                    'breed': record.breed_id.name,
                    'package': record.package_id.name,
                    'status': record.state
                })

        # Prepare the data dictionary for the report
        report_data = {
            'service_type': self.service_type,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'records': data
        }
        # Return the action to generate the PDF report
        return (self.env.ref('veterinary_management.action_veterinary_management_report').
                report_action(self, data=report_data))
