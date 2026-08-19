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
from odoo import api,fields,models,_
from odoo.exceptions import ValidationError


class SurgeryAppointment(models.Model):
    """Fields Needed to Surgery appointment"""
    _name = 'surgery.appointment'
    _description = 'Surgery Appointment'
    _rec_name = 'surgery_no'
    _inherit = 'mail.thread'

    surgery_no = fields.Char(string="surgery No", default=lambda self: _('New'),
                             copy=False, readonly=True, tracking=True)
    patient_id = fields.Many2one(string="Patient", comodel_name="case.appointments", help="Name of Patient",
                                 required=True)
    case_appointment_date = fields.Char(string="Appointment", related="patient_id.case_no",
                                        help="appointment")
    surgery_id = fields.Many2one(string="Surgery", comodel_name="surgery.types", help="Name of Surgery",
                                 required=True)
    urgency = fields.Char(string="Urgency", help="Urgency of surgery")
    company_id = fields.Many2one('res.company', store=True, copy=False,
                                 string="Company",
                                 default=lambda self: self.env.user.company_id.id)
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id)
    estimated_cost = fields.Float(string="Estimated Cost", related="surgery_id.charge",
                                  help="Estimated Cost of Surgery")
    desc = fields.Char(string="Description", help="Description of surgery")
    agreement = fields.Char(string="Agreement", help="mention the Agreement", tracking=True)
    scheduled_date = fields.Date(string="Schedule Date", help="Schedule date of surgery",copy="False",required=True)
    start_time = fields.Datetime(string="Start Time", copy="False",help="Start Time of surgery")
    end_time = fields.Datetime(string="End Time",copy="False", help="End Time of surgery")
    surgeon_id = fields.Many2one(string="Surgeon",
                              comodel_name="veterinary.employees",
                              domain=[('staff', '=', 'doctor')],
                              help="Surgeon of surgery",required=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('in-progress', 'In-Progress'),
                              ('complete', 'Complete')], default="draft", help="mention the state", tracking=True)

    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        """
                    Validate the appointment date to ensure it is not set before the current date.

                    This method is triggered when the 'appointment_date' field is changed.
                    It raises a ValidationError if the selected appointment date is earlier
                    than the current date and time.
                """
        for record in self:
            if record.scheduled_date and record.scheduled_date < fields.Date.today():
                raise ValidationError(_(
                    "Selected Surgery appointment date cannot be before today's date."))

    @api.model_create_multi
    def create(self, vals_list):
        """Function to assign surgery No"""
        for vals in vals_list:
            if vals.get('surgery_no', 'New') == 'New':
                vals['surgery_no'] = self.env['ir.sequence'].next_by_code('surgery.sequence') or 'New'
        return super().create(vals_list)
