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
from odoo import fields, models

class MedicalReportDetails(models.Model):
    """
        This model stores the details of medical reports associated with service-type products.

        It includes information about the medical report, such as the linked product (report),
        the date the report was created or updated, the lab technician responsible, the currency
        for pricing, the status of the report, and associated documents.
    """
    _name = 'medical.report.details'
    _description = 'Medical Report Details'

    report_id = fields.Many2one(
        string="Report",
        comodel_name="product.template",
        domain=[('type', '=', 'service'), ('is_medical_test', '=', True)],
        help="Select the medical report which is linked to a service type product."
    )
    date = fields.Date(
        string="Date",
        default=fields.Date.context_today,
        help="The date when the report was created or updated."
    )
    lab_technician_id = fields.Many2one(
        string="Lab Technician",
        comodel_name="res.partner",
        help="Lab technician responsible for this report."
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used for the pricing of the report."
    )
    document = fields.Binary(
        string="Document",
        help="Upload the document related to the medical report."
    )
    stages = fields.Selection([
        ('complete', 'Complete'),
        ('in-progress', 'In-Progress'),
        ('cancel', 'Cancel')],
        string="Status",
        default="in-progress",
        required=True,
        help="Current status of the medical report."
    )
    price = fields.Float(
        string="Price",
        related="report_id.list_price",
        help="Price of the medical report based on the related service."
    )
    medical_report_id = fields.Many2one(
        string="Appointment",
        comodel_name="case.appointments",
        help="Reference to the related case appointment."
    )


class ProcedureVaccineHistoryDetails(models.Model):
    """Model to store vaccination history of a patient."""
    _name = 'procedure.vaccine.history.details'
    _description = 'Procedure Vaccine History Details'

    vaccine_id = fields.Many2one(
        string="Vaccine",
        comodel_name="animal.vaccine",
        help="Select the vaccine administered to the patient."
    )
    vaccination_date = fields.Date(
        string="Vaccination Date",
        help="Date when the vaccination was administered to the patient."
    )
    description = fields.Char(
        string="Description",
        help="Description of the vaccination or any additional notes."
    )
    charge = fields.Float(
        string="charge",
        related="vaccine_id.charge",
        help="Charge of Vaccine injected to patient"
    )
    procedure_vaccine_history_id = fields.Many2one(
        string="Vaccine History",
        comodel_name="case.appointments",
        help="Reference to the related case appointment for the vaccination history."
    )
