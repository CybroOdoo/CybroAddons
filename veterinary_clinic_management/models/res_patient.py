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
import calendar
from datetime import datetime
from odoo import api, fields, models, _


class ResPatient(models.Model):
    """Model for storing details about animal patients in the veterinary clinic management system."""
    _name = 'res.patient'
    _description = 'Res Patient'
    _inherit = 'mail.thread'

    number = fields.Char(string="Sequence Number",
                         default=lambda self: _('New'),
                         copy=False,
                         readonly=True,
                         tracking=True,
                         help="Unique sequence number for identifying each patient.")
    name = fields.Char(string="Patient Name",
                       required=True,
                       help="Name of the animal patient.")
    photo = fields.Image(string='Photo', help="Photo of the Patient.")
    pet_type_id = fields.Many2one(string="Pet Type",
                                  comodel_name="animal.types",
                                  required=True,
                                  help="Type of animal (e.g., Dog, Cat).")
    breed_id = fields.Many2one(string="Breed",
                               comodel_name="breed.types",
                               help="Breed of the animal.")
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender', required=True, help="Gender of the animal.")
    age = fields.Integer(string="Age",
                         help="Age of the animal in years.",
                         required=True)
    behaviour = fields.Char(string="Behaviour",
                            help="Behavioral characteristics of the animal.")
    owner_name_id = fields.Many2one(string=" OwnerName",
                                    comodel_name="res.partner",
                                    required=True,
                                    help="Owner of the animal.")
    phone = fields.Char(string="phone",
                        related='owner_name_id.phone',
                        readonly=False,
                        help="Phone number of the animal's owner.")
    email = fields.Char(string="Email",
                        related='owner_name_id.email',
                        readonly=False,
                        help="Email address of the animal's owner.")
    color = fields.Char(string="Color",
                        help="Color of the animal.")
    height = fields.Float(string="Height",
                          help="Height of the animal in centimeters.")
    weight = fields.Float(string="Weight",
                          help="Weight of the animal in kilograms.")
    blood_type = fields.Selection([
        ('a_positive', 'A+'),
        ('a_negative', 'A-'),
        ('b_positive', 'B+'),
        ('b_negative', 'B-'),
        ('ab_positive', 'AB+'),
        ('ab_negative', 'AB-'),
        ('o_positive', 'O+'),
        ('o_negative', 'O-')
    ], string='Blood Type',
        help="Blood type of the animal.")
    rh = fields.Selection([
        ('positive', 'Positive'),
        ('negative', 'Negative')],
        string="RH",
        help="Rhesus factor of the animal's blood type.")
    medical_history_line_ids = fields.One2many(
        comodel_name="medical.history.details",
        inverse_name="medical_history_id",
        string="Medical History",
        help="Medical history records of the animal.")
    vaccination_history_line_ids = fields.One2many(
        comodel_name="vaccine.history.details",
        inverse_name="vaccine_history_id",
        string="Vaccination History",
        help="Vaccination history records of the animal.")
    training_count = fields.Integer(
        string="Training",
        compute='_compute_training_count',
        default=0,
        help="Count of training records for the animal."
    )
    grooming_count = fields.Integer(
        string="Grooming",
        compute='_compute_grooming_count',
        default=0,
        help="Count of grooming records for the animal."
    )
    procedure_count = fields.Integer(
        string="Procedure",
        compute='_compute_procedure_count',
        default=0,
        help="Count of medical procedures for the animal."
    )
    surgery_count = fields.Integer(
        string="Surgery",
        compute='_compute_surgery_count',
        default=0,
        help="Count of surgeries performed on the animal."
    )
    prescription_count = fields.Integer(
        string="Prescription",
        compute='_compute_prescription_count',
        default=0,
        help="Count of prescriptions issued for the animal."
    )

    def _compute_training_count(self):
        """
        Compute the number of training sessions attended by the animal.
        """
        for record in self:
            record.training_count = self.env['animal.training'].search_count([('animal_id', '=', record.id)])

    def _compute_grooming_count(self):
        """
        Compute the number of grooming sessions attended by the animal.
        """
        for record in self:
            record.grooming_count = self.env['animal.grooming'].search_count([('patient_name_id', '=', record.id)])

    def _compute_procedure_count(self):
        """
        Compute the number of medical procedures undergone by the animal.
        """
        for record in self:
            record.procedure_count = self.env['case.appointments'].search_count([('patient_id', '=', record.id)])

    def _compute_surgery_count(self):
        """
        Compute the number of surgeries undergone by the animal.
        """
        for record in self:
            record.surgery_count = self.env['surgery.appointment'].search_count([('patient_id', '=', record.id)])

    def _compute_prescription_count(self):
        """
        Compute the number of prescriptions issued for the animal.
        """
        for record in self:
            record.prescription_count = self.env['prescription.orders'].search_count([('patient_id', '=', record.id)])

    def action_get_training_record(self):
        """
        Open the training records related to the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Training Sessions',
            'view_mode': 'list,form',
            'res_model': 'animal.training',
            'domain': [('animal_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_get_grooming_record(self):
        """
        Open the grooming records related to the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Grooming Sessions',
            'view_mode': 'list,form',
            'res_model': 'animal.grooming',
            'domain': [('patient_name_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_get_procedure_record(self):
        """
        Open the medical procedure records related to the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Medical Procedures',
            'view_mode': 'list,form',
            'res_model': 'case.appointments',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_get_surgery_record(self):
        """
        Open the surgery records related to the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Surgeries',
            'view_mode': 'list,form',
            'res_model': 'surgery.appointment',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_get_prescription_record(self):
        """
        Open the prescription records related to the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Prescriptions',
            'view_mode': 'list,form',
            'res_model': 'prescription.orders',
            'domain': [('patient_id', '=', self.id)],
            'context': "{'create': True}"
        }

    def action_create_appointment(self):
        """
        Create a new appointment for the animal.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Appointment',
            'res_model': 'veterinary.appointment',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {
                'default_patient': self.id,
            },
            'target': 'new'
        }

    @api.model
    def get_count_data(self):
        """
        Fetches and returns various counts related to veterinary clinic management data.

        Returns:
            dict: A dictionary containing the following counts:
                - 'total_grooming': Total count of grooming sessions.
                - 'total_procedure': Total count of medical procedures.
                - 'total_training': Total count of training sessions.
                - 'total_doctors': Total count of doctors.
                - 'total_nurses': Total count of nurses.
                - 'total_surgeries': Total count of surgeries.
                - 'today_grooming': Count of grooming sessions scheduled for today.
                - 'today_procedure': Count of medical procedures scheduled for today.
                - 'today_training': Count of training sessions scheduled for today.
                - 'today_doctors': Count of available doctors for today.
                - 'today_nurses': Count of available nurses for today.
                - 'today_surgeries': Count of surgeries scheduled for today.
        """
        grooming = self.env['animal.grooming'].search_count([])
        procedure = self.env['case.appointments'].search_count([])
        training = self.env['animal.training'].search_count([])
        doctors = self.env['veterinary.employees'].search_count([('staff', '=', 'doctor')])
        nurses = self.env['veterinary.employees'].search_count([('staff', '=', 'nurse')])
        surgeries = self.env['surgery.appointment'].search_count([])
        today_grooming = self.env['animal.grooming'].search_count([('appointment_date', '=', fields.Date.today())])
        today_procedure = self.env['case.appointments'].search_count([('appointment_date', '=', fields.Date.today())])
        today_training = self.env['animal.training'].search_count([('appointment_date', '=', fields.Date.today())])


        # Get today's weekday
        today_day = datetime.now().strftime('%A').lower() + '_available'

        # Count available doctors for today
        today_doctors = self.env['veterinary.employees'].search_count([
            ('staff', '=', 'doctor'),
            (today_day, '=', True)
        ])
        # Count available nurses for today
        today_nurses = self.env['veterinary.employees'].search_count([
            ('staff', '=', 'nurse'),
            (today_day, '=', True)
        ])
        today_surgeries = self.env['surgery.appointment'].search_count([('scheduled_date', '=', fields.Date.today())])

        return {
            'total_grooming': grooming,
            'total_procedure': procedure,
            'total_training': training,
            'total_doctors': doctors,
            'total_nurses': nurses,
            'total_surgeries': surgeries,
            'today_grooming': today_grooming,
            'today_procedure': today_procedure,
            'today_training': today_training,
            'today_doctors': today_doctors,
            'today_nurses': today_nurses,
            'today_surgeries': today_surgeries,
        }

    def get_monthly_appointments(self):
        """This function get data of count of appointment for procedure,grooming,training for
         plot the graph in dashboard """
        # Calculate start and end date for the current month
        today = fields.Date.today()
        start_date = today.replace(day=1)
        end_date = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        # Counting records
        procedure_count = self.env['case.appointments'].search_count([('appointment_date', '>=', start_date),
                                                                      ('appointment_date', '<=', end_date)])
        grooming_count = self.env['animal.grooming'].search_count([('appointment_date', '>=', start_date),
                                                                   ('appointment_date', '<=', end_date)])
        training_count = self.env['animal.training'].search_count([('appointment_date', '>=', start_date),
                                                                   ('appointment_date', '<=', end_date)])
        products = ['procedure', 'Grooming', 'Training']
        counts = [procedure_count, grooming_count, training_count]
        result = {'products': products, 'count': counts}
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Assign a unique appointment number when creating a new patient record."""
        for vals in vals_list:
          if vals.get('number', 'New') == 'New':
            vals['number'] = self.env['ir.sequence'].next_by_code('appointment.sequence') or 'New'
        return super().create(vals_list)

