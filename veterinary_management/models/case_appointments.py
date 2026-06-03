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
from odoo import  api,fields, models, _
from odoo.exceptions import ValidationError


class CaseAppointments(models.Model):
    """Fields Needed to create appointment"""
    _name = 'case.appointments'
    _description = 'Case Appointments'
    _rec_name = 'patient_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    case_no = fields.Char(
        string="Case No",
        default=lambda self: _('New'),
        copy=False,
        readonly=True,
        tracking=True,
        help="Unique identifier for the case appointment"
    )
    patient_id = fields.Many2one(
        string="Patient",
        comodel_name="res.patient",
        required=True,
        ondelete='cascade',
        help="Reference to the patient"
    )
    owner_id = fields.Many2one(
        string="Owner",
        related="patient_id.owner_name_id",
        help="Owner of the patient (e.g., pet owner)"
    )
    doctor_id = fields.Many2one(
        string="Doctor",
        comodel_name="veterinary.employees",
        domain=[('staff', '=', 'doctor')],
        required=True,
        help="Consulting doctor for the appointment"
    )
    appointment_date = fields.Date(
        string="Appointment Date",
        default=fields.Date.today,
        help="Close Date of the appointment"
    )
    closed_date = fields.Date(
        string="Closed Date",
        help="Date of the appointment"
    )
    nurse_id = fields.Many2one(
        string="Nurse",
        comodel_name="veterinary.employees",
        domain=[('staff', '=', 'nurse')],
        context={'default_staff': 'nurse'},
        help="Nurse attending the appointment"
    )
    treatment = fields.Boolean(
        string="Treatment",
        store=True,
        help="Indicate if treatment is provided"
    )
    vaccination = fields.Boolean(
        string="Vaccination",
        store=True,
        help="Indicate if vaccination is administered"
    )
    is_admit = fields.Boolean(
        string="Is Admit",
        store=True,
        help="Indicate if the patient is admitted"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in-consultation', 'In Consultation'),
        ('close', 'Close'),
        ('cancel', 'Cancel'),
    ],
        default="draft",
        tracking=True,
        help="Current state of the appointment"
    )
    disease_name_ids = fields.Many2many(
        string="Disease Name",
        comodel_name="disease.types",
        help="List of diseases diagnosed"
    )
    disease_desc = fields.Html(
        string="Disease Description",
        help="Detailed description of the disease"
    )
    room_id = fields.Many2one(
        string="Room",
        comodel_name="room.details",
        help="Assigned room for the patient"
    )
    admit_date = fields.Date(
        string="Admit Date",
        default=fields.Date.today,
        help="Date of admission"
    )
    total_hours = fields.Float(
        string="Total Hours",
        help="Total hours the patient is admitted"
    )
    table_no = fields.Char(
        string="Table No",
        help="Table number for the appointment"
    )
    discharge_date = fields.Date(
        string="Discharge Date",
        help="Date of discharge"
    )
    room_charge = fields.Float(
        string="Room Charge",
        related="room_id.charge",
        help="Charge for the room"
    )
    total_amount = fields.Float(
        string="Total Amount",
        compute='_compute_total_admit_amount',
        help="Total amount for the admission"
    )
    treatment_line_ids = fields.One2many(
        comodel_name="treatment.line.details",
        inverse_name="treatment_id",
        string="Treatment",
        copy="False",
        help="Details of the treatment provided"
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency used for billing"
    )
    treatment_total = fields.Monetary(
        string="Total",
        compute="_compute_treatment_total",
        help="Total cost of the treatment"
    )
    vaccine_total = fields.Monetary(
        string="Total",
        compute="_compute_vaccine_total",
        help="Total cost of the vaccines injected to patient"
    )
    medical_report_line_ids = fields.One2many(
        comodel_name="medical.report.details",
        inverse_name="medical_report_id",
        string="Medical Report",
        copy="False",
        help="Medical report details"
    )
    procedure_vaccination_history_line_ids = fields.One2many(
        comodel_name="procedure.vaccine.history.details",
        inverse_name="procedure_vaccine_history_id",
        string="Vaccination",
        copy="False",
        help="List of vaccines taken by patient"

    )
    medical_bill_line_ids = fields.One2many(
        comodel_name="medical.bill.details",
        inverse_name="medical_bill_id",
        string="Medical Bill",
        copy="False",
        help="Details of the medical bill"
    )
    medical_bill_invoice_id = fields.Many2one(
        comodel_name='account.move',
        copy="False",
        help="Reference to the medical bill invoice"
    )
    is_invoice = fields.Boolean(
        help="Indicate if an invoice has been created"
    )
    invoice_count = fields.Integer(
        compute="_compute_invoice_count",
        help="Count of invoices generated"
    )
    payment_ribbon = fields.Char(
        compute='_compute_payment_ribbon',
        help="Payment status of the invoice"
    )
    surgery_count = fields.Integer(
        string="Surgery",
        compute='_compute_surgery_count',
        default=0,
        help="Count of surgeries scheduled"
    )
    prescription_count = fields.Integer(
        string="Prescription",
        compute='_compute_prescription_count',
        default=0,
        help="Count of prescriptions issued"
    )

    @api.depends('total_hours', 'room_charge')
    def _compute_total_admit_amount(self):
        """Compute total amount for admission based on hours and room charge"""
        for rec in self:
            rec.total_amount = rec.total_hours * rec.room_charge

    def _compute_invoice_count(self):
        """Compute the count of invoices"""
        for rec in self:
            rec.invoice_count = len(rec.medical_bill_invoice_id)

    @api.depends('medical_bill_invoice_id.payment_state', )
    def _compute_payment_ribbon(self):
        """Compute payment status for the ribbon"""
        for record in self:
            record.payment_ribbon = record.medical_bill_invoice_id.payment_state

    @api.depends('treatment_line_ids.charges')
    def _compute_treatment_total(self):
        """Compute the total cost of all treatments"""
        for record in self:
            record.treatment_total = sum(record.treatment_line_ids.mapped('charges'))

    @api.depends('procedure_vaccination_history_line_ids.charge')
    def _compute_vaccine_total(self):
        """Compute the total cost of all vaccines injected to patient"""
        for record in self:
            record.vaccine_total = sum(record.procedure_vaccination_history_line_ids.mapped('charge'))

    def _compute_surgery_count(self):
        """Compute the count of surgeries scheduled"""
        for record in self:
            record.surgery_count = self.env['surgery.appointment'].search_count(
                [('patient_id', '=', self.id)])

    def _compute_prescription_count(self):
        """Compute the count of prescriptions issued"""
        for record in self:
            record.prescription_count = self.env['prescription.orders'].search_count(
                [('patient_id', '=', self.id)])

    @api.onchange('appointment_date')
    def _onchange_appointment_date(self):
        """
            Validate the appointment date to ensure it is not set before the current date.

            This method is triggered when the 'appointment_date' field is changed.
            It raises a ValidationError if the selected appointment date is earlier
            than the current date and time.
            """
        if self.appointment_date < fields.Date.today():
            raise ValidationError(_(
                "Selected appointment date cannot be before today's date."))

    def action_get_surgery_record(self):
        """Action to view surgery records"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Surgery',
            'view_mode': 'tree,form',
            'res_model': 'surgery.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_get_prescription_record(self):
        """Action to view prescription records"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prescription',
            'view_mode': 'tree,form',
            'res_model': 'prescription.orders',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    @api.model
    def create(self, vals_list):
        """Function to assign Appointment No"""
        if vals_list.get('case_no', 'New') == 'New':
            vals_list['case_no'] = self.env['ir.sequence'].next_by_code('case.sequence') or 'New'
        return super().create(vals_list)

    def action_confirm(self):
        """Confirm the appointment"""
        self.state = 'in-consultation'

    def action_cancel(self):
        """Cancel the appointment"""
        self.state = 'cancel'

    def action_create_prescription(self):
        """Action to create a new prescription"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Prescription',
            'res_model': 'prescription.orders',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_patient_id': self.patient_id.id,
                'default_doctor_id': self.doctor_id.id,
            },
            'target': 'new'
        }

    def action_schedule_surgery(self):
        """Action to create a new surgery appointment"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Surgery',
            'res_model': 'surgery.appointment',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_patient_id': self.id,
            },
            'target': 'new'
        }

    def action_create_medical_report(self):
        """Action to create a new medical report appointment"""
        for rec in self.medical_report_line_ids:
            existing_report = rec.env['medical.report'].search([
                ('patient_id', '=', self.id),
                ('report_type_id', '=', rec.report_id.id),
                ('lab_technician_id', '=', rec.lab_technician_id.id),
                ('report_date', '=', rec.date),
            ], limit=1)
            if not existing_report:
                rec.env['medical.report'].create({
                    'patient_id': self.id,
                    'report_type_id': rec.report_id.id,
                    'price': rec.price,
                    'lab_technician_id': rec.lab_technician_id.id,
                    'report_date': rec.date,
                    'document': rec.document,
                })

    def action_create_invoice(self):
        """Function to create invoice for medical bill"""
        invoice = self.env['account.move'].create([
            {
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(self),
                'partner_id': self.owner_id.id,
                'currency_id': self.currency_id.id,
                'medical_bill_invoice_id': self.id
            }])
        for record in self.medical_bill_line_ids:
            invoice.write({
                'invoice_line_ids': [(0, 0, {
                    'product_id': line.service_type_id.id,
                    'name': line.service_type_id.name,
                    # 'quantity': line.quantity,
                    'price_unit': line.amount,
                }) for line in record]
            })
        self.medical_bill_invoice_id = invoice.id
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
        """Function to view invoices in invoice smart button"""
        return {
            'name': 'Customer Invoices',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.medical_bill_invoice_id.id
        }


class TreatmentLineDetails(models.Model):
    """Class for treatment line details"""
    _name = 'treatment.line.details'
    _description = 'Treatment Line Details'

    description = fields.Char(
        string="Description",
        help="Description of the treatment provided"
    )
    precaution = fields.Char(
        string="Precaution",
        help="Precautions to be taken for the treatment"
    )
    currency_id = fields.Many2one(
        string="Currency",
        comodel_name="res.currency",
        default=lambda self: self.env.company.currency_id.id,
        help="Currency in which the charges are calculated"
    )
    charges = fields.Monetary(
        string="Charges",
        currency_field='currency_id',
        help="Cost of the treatment in the specified currency"
    )
    treatment_id = fields.Many2one(
        string="Treatment",
        comodel_name="case.appointments",
        help="Reference to the related case appointment"
    )


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
        domain=[('detailed_type', '=', 'service'), ('medical_report', '=', True)],
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


class MedicalBillDetails(models.Model):
    """Model to store medical bill details."""
    _name = 'medical.bill.details'
    _description = 'Medical Bill Details'

    service_type_id = fields.Many2one(
        string="Service Type",
        comodel_name="product.product",
        domain=[('medical_bill_product', '=', True)],
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
