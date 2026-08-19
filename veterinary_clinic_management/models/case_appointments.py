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
from odoo import api, fields, models, _, Command
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
    is_treated = fields.Boolean(
        string="Treated",
        store=True,
        help="Indicates whether treatment was provided."
    )
    is_vaccinated = fields.Boolean(
        string="Vaccinated",
        store=True,
        help="Indicates whether the patient has been vaccinated."
    )
    is_admitted = fields.Boolean(
        string="Admitted",
        store=True,
        help="Indicates whether the patient is admitted."
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
        compute='_compute_total_amount',
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
    is_invoiced = fields.Boolean(
        string="Invoiced",
        help="Indicates whether an invoice has been created."
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
    def _compute_total_amount(self):
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
            'view_mode': 'list,form',
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
            'view_mode': 'list,form',
            'res_model': 'prescription.orders',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Function to assign Appointment No"""
        for vals in vals_list:
            if vals.get('case_no', 'New') == 'New':
                vals['case_no'] = self.env['ir.sequence'].next_by_code('case.sequence') or 'New'
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
                'default_patient_id': self.id,
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
        """Create an invoice."""
        for record in self:
            lines = [Command.create({
                'product_id': line.service_type_id.id,
                'name': line.service_type_id.name,
                'price_unit': line.amount,
            }) for line in record.medical_bill_line_ids]

            if not lines:
                raise ValidationError(_("Please add at least one service before creating an invoice."))

            invoice = self.env['account.move'].create([{
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.context_today(record),
                'partner_id': record.owner_id.id,
                'currency_id': record.currency_id.id or self.env.company.currency_id.id,
                'medical_bill_invoice_id': record.id,
                'invoice_line_ids': lines
            }])
            record.medical_bill_invoice_id = invoice.id
            record.is_invoiced = True
            return {
                'name': _('Customer Invoices'),
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'context': {'default_move_type': 'out_invoice'},
                'type': 'ir.actions.act_window',
                'target': 'new',
                'res_id': invoice.id
            }

    def action_view_invoice(self):
        """Action to view the created invoice."""
        self.ensure_one()
        return {
            'name': _('Customer Invoices'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'context': {'default_move_type': 'out_invoice'},
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.medical_bill_invoice_id.id
        }
