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


class MedicalReport(models.Model):
    """Model to store medical report details."""
    _name = 'medical.report'
    _description = 'Medical Report'
    _rec_name = 'case_id'
    _inherit = 'mail.thread'

    patient_id = fields.Many2one(
        'case.appointments',
        string='Patient',
        help="Reference to the patient associated with the medical report.", required=True
    )
    case_id = fields.Char(
        string="Case No",
        related="patient_id.case_no",
        help="The unique case number related to the patient."
    )
    report_type_id = fields.Many2one(
        string="Report",
        comodel_name="product.template",
        help="Type of medical report.",
        domain=[('detailed_type', '=', 'service'), ('medical_report', '=', True)], required=True
    )
    company_id = fields.Many2one(
        'res.company',
        string="Company",
        store=True,
        copy=False,
        default=lambda self: self.env.user.company_id.id,
        help="The company associated with this medical report."
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id',
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Currency used for the medical report."
    )
    price = fields.Float(
        string='Price',
        related="report_type_id.list_price",
        help="Price of the medical report."
    )
    document = fields.Binary(
        string='Document',
        copy="False",
        help="Attached document for the medical report."
    )
    report_date = fields.Date(
        string='Date',
        default=fields.Date.today,
        copy="False",
        help="Date when the medical report was created."
    )
    lab_technician_id = fields.Many2one(
        'res.partner',
        string='Lab Technician',
        copy="False",
        help="The lab technician responsible for the report.", required=True
    )
    pet_name_id = fields.Many2one(
        related="patient_id.patient_id",
        string='Pet Name',
        help="Name of the pet associated with the patient."
    )
    pet_type = fields.Many2one(
        string="Pet Type",
        related="patient_id.patient_id.pet_type_id",
        help="Type of pet (e.g., dog, cat)."
    )
    breed_id = fields.Many2one(
        string='Breed',
        related="patient_id.patient_id.breed_id",
        help="Breed of the pet."
    )
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        string='Gender',
        related="patient_id.patient_id.gender",
        help="Gender of the pet."
    )
    age = fields.Integer(
        string='Age',
        related="patient_id.patient_id.age",
        help="Age of the pet in years."
    )
    behavior = fields.Char(
        string='Behavior',
        related="patient_id.patient_id.behaviour",
        help="Behavioral traits of the pet."
    )
    weight = fields.Float(
        string='Weight',
        related="patient_id.patient_id.weight",
        help="Weight of the pet in kilograms."
    )
    height = fields.Float(
        string='Height',
        related="patient_id.patient_id.height",
        help="Height of the pet in centimeters."
    )
    blood_type = fields.Selection(
        [('a_positive', 'A+'), ('a_negative', 'A-'), ('b_positive', 'B+'),
         ('b_negative', 'B-'), ('ab_positive', 'AB+'), ('ab_negative', 'AB-'),
         ('o_positive', 'O+'), ('o_negative', 'O-')],
        string='Blood Type',
        related="patient_id.patient_id.blood_type",
        help="Blood type of the pet."
    )
    rh = fields.Selection(
        [('positive', 'Positive'), ('negative', 'Negative')],
        string='RH Factor',
        related="patient_id.patient_id.rh",
        help="RH factor of the pet's blood."
    )
    state = fields.Selection(
        [('new', 'New'), ('in-progress', 'In-Progress'), ('complete', 'Complete')],
        default="new",
        help="Current state of the medical report.",
        tracking=True
    )
    medical_report_invoice_id = fields.Many2one(
        comodel_name='account.move',
        string="Invoice",
        help="The invoice associated with this medical report."
    )
    is_invoice = fields.Boolean(
        string='Is Invoice',
        help="Indicator whether an invoice has been created for this report."
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        string='Invoice Count',
        help="Number of invoices related to this medical report."
    )
    payment_ribbon = fields.Char(
        compute='_compute_payment_ribbon',
        string='Payment Status',
        help="Payment status ribbon for the invoice."
    )

    @api.depends('medical_report_invoice_id')
    def _compute_invoice_count(self):
        """Compute the count of invoices for the medical report."""
        for rec in self:
            rec.invoice_count = len(rec.medical_report_invoice_id)

    @api.depends('medical_report_invoice_id')
    def _compute_payment_ribbon(self):
        """Compute the payment status badge for the report."""
        for record in self:
            record.payment_ribbon = record.medical_report_invoice_id.payment_state

    def action_confirm(self):
        """Set the report state to 'In-Progress'."""
        self.state = 'in-progress'

    def create_invoice(self):
        """Create an invoice for the medical report."""
        for record in self:
            product = self.env['product.product'].search([('product_tmpl_id', '=', record.report_type_id.id)], limit=1)
            invoice = self.env['account.move'].create([
                {
                    'move_type': 'out_invoice',
                    'invoice_date': fields.Date.context_today(self),
                    'partner_id': self.patient_id.owner_id.id,
                    'currency_id': self.currency_id.id,
                    'medical_test_bill_invoice_id': self.id,
                    'invoice_line_ids': [(0, 0, {
                        'product_id': product.id,
                        'name': record.report_type_id.name,
                        'price_unit': record.price,
                    }) for line in record]
                }])
            self.medical_report_invoice_id = invoice.id
            self.is_invoice = True
            return {
                'name': 'Customer Invoices',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'context': {'default_move_type': 'out_invoice'},
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': invoice.id

            }

    def action_view_invoice(self):
        """Open the form view of the invoice related to this report."""
        return {
            'name': 'Customer Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.medical_report_invoice_id.id
        }
