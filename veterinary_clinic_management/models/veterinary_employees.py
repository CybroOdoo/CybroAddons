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
from odoo import api, models, fields


class VeterinaryEmployees(models.Model):
    """
       Model to store details of staff, including their personal information,
       specialization, availability, and related statistics.
    """
    _name = 'veterinary.employees'
    _description = 'Veterinary Employee'

    name = fields.Char(string='Name',copy="False", required=True, help="Name of the staff.")
    staff = fields.Selection(
        [('doctor', 'Doctor'), ('nurse', 'Nurse'), ('support_staff', 'Support Staff')],
        string="Staff",
        default="doctor",
        help="Role of the staff member."
    )
    photo = fields.Image(string='Photo',copy="False", help="Photo of the staff member.")
    related_partner_id = fields.Many2one(
        string="Related Partner",
        comodel_name="res.partner",
        help="Related partner record."
    )
    gender = fields.Selection(
        [('male', 'Male'), ('female', 'Female')],
        string='Gender',
        help="Gender of the staff member."
    )
    birth_date = fields.Date(string='Birth Date', help="Birth date of the staff member.")
    phone = fields.Char(string='Phone', help="Phone number.")
    email = fields.Char(string='Email', help="Email address.")

    @api.onchange('related_partner_id')
    def _onchange_related_partner_id(self):
        """Auto-fill phone and email from the selected related partner.
        Gender and birth date are not available here since res.partner
        (Contacts) does not carry those fields unless the hr module is
        installed, so they remain manual entry."""
        if self.related_partner_id:
            self.phone = self.related_partner_id.phone
            self.email = self.related_partner_id.email
    specialization_ids = fields.Many2many(
        string='Specialization',
        comodel_name="animal.types",
        help="Specializations of the staff member."
    )
    license_number = fields.Char(string='Licence',copy="False", help="Licence number of the staff member.")
    degrees = fields.Char(string='Degrees',copy="False", help="Degrees and qualifications of the staff member.")
    company_id = fields.Many2one(
        'res.company',
        store=True,
        copy=False,
        string="Company",
        default=lambda self: self.env.user.company_id.id,
        help="Company the staff member is associated with."
    )
    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        related='company_id.currency_id',
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Currency used for consultancy charges."
    )
    consultancy_charges = fields.Monetary(string='Consultancy Charges',copy="False", help="Consultancy charges.")
    consultancy_type = fields.Selection(
        [('hospital', 'Hospital'), ('clinic', 'Clinic')],
        string='Consultancy Type',
        help="Type of consultancy (hospital or clinic)."
    )
    appointment_duration = fields.Float(string='Duration of Appointment', help="Duration of appointments in hours.")
    sunday_available = fields.Boolean(string="Sunday", help="Availability on Sunday.")
    monday_available = fields.Boolean(string="Monday", help="Availability on Monday.")
    tuesday_available = fields.Boolean(string="Tuesday", help="Availability on Tuesday.")
    wednesday_available = fields.Boolean(string="Wednesday", help="Availability on Wednesday.")
    thursday_available = fields.Boolean(string="Thursday", help="Availability on Thursday.")
    friday_available = fields.Boolean(string="Friday", help="Availability on Friday.")
    saturday_available = fields.Boolean(string="Saturday", help="Availability on Saturday.")
    case_count = fields.Integer(
        string="Case",
        compute='_compute_case_count',
        default=0,
        help="Total number of cases handled by the staff member."
    )
    today_case_count = fields.Integer(
        string="Today Cases",
        compute='_compute_today_case_count',
        default=0,
        help="Number of cases handled by the staff member today."
    )
    surgery_count = fields.Integer(
        string="Surgery",
        compute='_compute_surgery_count',
        default=0,
        help="Total number of surgeries performed by the staff member."
    )
    today_surgery_count = fields.Integer(
        string="Today Surgery",
        compute='_compute_today_surgery_count',
        default=0,
        help="Number of surgeries performed by the staff member today."
    )
    def _compute_case_count(self):
        """
            Computes the total number of cases handled by the staff member.
        """
        for record in self:
            record.case_count = self.env['case.appointments'].search_count(
                [('doctor_id', '=', self.id)])

    def _compute_today_case_count(self):
        """
            Computes the number of cases handled by the staff member today.
        """
        for record in self:
            record.today_case_count = self.env['case.appointments'].search_count(
                [('doctor_id', '=', self.id), ('appointment_date', '=', fields.Date.today())])

    def _compute_surgery_count(self):
        """
            Computes the total number of surgeries performed by the staff member.
        """
        for record in self:
            record.surgery_count = self.env['surgery.appointment'].search_count(
                [('surgeon_id', '=', self.id)])

    def _compute_today_surgery_count(self):
        """
            Computes the number of surgeries performed by the staff member today.
        """
        for record in self:
            record.today_surgery_count = self.env['surgery.appointment'].search_count(
                [('surgeon_id', '=', self.id), ('scheduled_date', '=', fields.Date.today())])

    def action_get_case_record(self):
        """
                Returns an action to open the cases handled by the staff member.

                The action opens a window with the list of case appointments where the staff member is involved.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Case',
            'view_mode': 'list,form',
            'res_model': 'case.appointments',
            'domain': [('doctor_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_today_case_record(self):
        """
            Returns an action to open the cases handled by the staff member today.

            The action opens a window with the list of today's case appointments where the staff member is involved.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Today Case',
            'view_mode': 'list,form',
            'res_model': 'case.appointments',
            'domain': [('doctor_id', '=', self.id), ('appointment_date', '=', fields.Date.today())],
            'context': "{'create': False}"
        }

    def action_get_surgery_record(self):
        """
            Returns an action to open the surgeries performed by the staff member.

            The action opens a window with the list of surgery appointments where the staff member is the surgeon.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Surgery',
            'view_mode': 'list,form',
            'res_model': 'surgery.appointment',
            'domain': [('surgeon_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def action_get_today_surgery_record(self):
        """
            Returns an action to open the surgeries performed by the staff member today.

            The action opens a window with the list of today's surgery appointments where the staff member is the surgeon.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Today Surgery',
            'view_mode': 'list,form',
            'res_model': 'surgery.appointment',
            'domain': [('surgeon_id', '=', self.id), ('scheduled_date', '=', fields.Date.today())],
            'context': "{'create': False}"
        }