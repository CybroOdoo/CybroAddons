# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class MedicalBillDetails(models.Model):
    """Model to store medical bill details."""
    _name = 'medical.bill.details'
    _description = 'Medical Bill Details'

    service_type_id = fields.Many2one(
        string="Service Type",
        comodel_name="product.product",
        domain=[('is_medical_bill_product', '=', True)],
        help="Select the type of service that is billed. Only services marked for medical bills are available."
    )
    invoice_for = fields.Char(
        string="Invoice For",
        help="The type of invoice, such as 'Doctor Charges', 'Treatment', 'Patient Admit', or 'Surgery Charges'."
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        help="The date on which the service was provided or billed."
    )
    description = fields.Text(
        string="Description",
        help="Description of the service provided or any additional details related to the billing."
    )
    amount = fields.Float(
        string="Amount",
        help="Total amount for the service provided."
    )
    medical_bill_id = fields.Many2one(
        string="Medical Bill",
        comodel_name="case.appointments",
        help="Reference to the related case appointment for this medical bill."
    )

    @api.onchange('service_type_id')
    def _onchange_service_type(self):
        """Automatically set invoice details based on selected service type."""
        if self.service_type_id.name == 'Consultancy':
            self.invoice_for = 'Doctor Charges'
            self.description = f'Consultancy charges of {self.medical_bill_id.doctor_id.name}'
            self.amount = self.medical_bill_id.doctor_id.consultancy_charges
        elif self.service_type_id.name == 'Treatment':
            self.invoice_for = 'Treatment'
            self.description = 'Treatment provided including medications and procedures.'
            self.amount = self.medical_bill_id.treatment_total
        elif self.service_type_id.name == 'Vaccines':
            self.invoice_for = 'Vaccines'
            self.description = 'Vaccines provided including medications and procedures.'
            self.amount = self.medical_bill_id.vaccine_total
        elif self.service_type_id.name == 'Admit':
            self.invoice_for = 'Patient Admit'
            self.description = 'Admit charges for patient care.'
            self.amount = self.medical_bill_id.total_amount
        elif self.service_type_id.name == 'Surgery':
            surgery_appointment_check = self.env['surgery.appointment'].search([
                ('case_appointment_date', '=', self.medical_bill_id.case_no)])
            self.invoice_for = 'Surgery Charges'
            self.description = 'Charges for surgical procedures.'
            self.amount = surgery_appointment_check.estimated_cost

    @api.constrains('service_type_id', 'medical_bill_id')
    def _check_service_type_uniqueness(self):
        """Check that the same service type is not repeated in the same medical bill."""
        for record in self:
            if record.service_type_id:
                existing_records = self.env['medical.bill.details'].search([
                    ('medical_bill_id', '=', record.medical_bill_id.id),
                    ('service_type_id', '=', record.service_type_id.id),
                    ('id', '!=', record.id),  # Exclude current record
                ])
                if existing_records:
                    raise ValidationError(_(
                        "The service type '%s' is already added to this medical bill. "
                        "Please remove it.") % record.service_type_id.name)