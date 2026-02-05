# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, fields, models, _


class DentalAppointment(models.Model):
    """Patient dental appointment details"""
    _name = 'dental.appointment'
    _description = "Dental Appointment for patients"
    _inherit = "mail.thread"
    _rec_name = 'sequence_no'

    sequence_no = fields.Char(string='Sequence No', readonly=True,
                              default=lambda self: self.env._('New'),
                              copy=False,
                              help="Sequence number of appointment")
    token_no = fields.Integer(string='Token No', copy=False,
                              readonly=True,
                              help="Token number of the appointments")
    patient_id = fields.Many2one('res.partner',
                                 string="Patient Name",
                                 domain="[('is_patient', '=', True)]",
                                 copy=False,
                                 required=True,
                                 help="Add the patient")
    patient_phone = fields.Char(related="patient_id.phone", string="Phone",
                                help="Phone number of the patient")
    patient_age = fields.Integer(related="patient_id.patient_age", string="Age",
                                 help="Age of the patient")
    specialist_id = fields.Many2one('dental.specialist',
                                    string="Doctors Department",
                                    help='Choose the doctors department')
    doctor_ids = fields.Many2many('hr.employee',
                                  compute='_compute_doctor_ids',
                                  string="Doctors Data", help="Doctors Data")
    doctor_id = fields.Many2one('hr.employee', string="Doctor",
                                required=True,
                                domain="[('id', 'in', doctor_ids)]",
                                help="Name the of the doctor")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift",
                                      help="Choose the time shift",
                                      compute='_compute_time_shifts')
    shift_id = fields.Many2one('dental.time.shift',
                               string="Booking Time",
                               domain="[('id','in',time_shift_ids)]",
                               help="Choose the time shift")
    date = fields.Date(string="Date", required=True,
                       default=fields.date.today(),
                       help="Date when to take appointment for doctor")
    reason = fields.Text(string="Please describe the reason",
                         help="Just explain about the reason to take doctor appointment")
    state = fields.Selection([('draft', 'Draft'),
                              ('new', 'New Appointment'),
                              ('done', 'Prescribed'),
                              ('cancel', 'Cancel')],
                             default="draft",
                             string="State", help="state of the appointment")

    @api.model
    def create(self, vals):
        """Function declared for creating sequence Number for Appointments"""
        if vals.get('sequence_no', self.env._('New')) == self.env._('New'):
            vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                'dental.appointment') or self.env._('New')
        last_token = self.search(
            [('doctor_id', '=', int(vals['doctor_id'])),
             ('date', '=', vals['date']),
             ('shift_id', '=', int(vals['shift_id']))],
            order='id desc', limit=1)
        vals['token_no'] = last_token.token_no + 1 if last_token else 1
        res = super(DentalAppointment, self).create(vals)
        res.state = 'new'
        return res

    def action_create_appointment(self):
        """Change the state of the appointment while click create button"""
        self.state = 'new'

    @api.depends('doctor_id')
    def _compute_time_shifts(self):
        """To get the doctors time shift"""
        for record in self:
            record.time_shift_ids = self.env['dental.time.shift'].search(
                [('id', 'in', record.doctor_id.time_shift_ids.ids)]).ids

    @api.depends('specialist_id')
    def _compute_doctor_ids(self):
        """Searching for doctors based on there specialization"""
        for record in self:
            if record.specialist_id:
                record.doctor_ids = self.env['hr.employee'].search(
                    [('specialised_in_id', '=', record.specialist_id.id)]).ids
            else:
                record.doctor_ids = self.env['hr.employee'].search([]).ids

    def action_cancel(self):
        """Change the state of the appointment while click cancel button"""
        self.state = 'cancel'

    def action_prescription(self):
        """Created the action for view the prescriptions
        of 'done' state appointments"""
        return {
            'type': 'ir.actions.act_window',
            'target': 'inline',
            'name': 'Prescription',
            'view_mode': 'form',
            'res_model': 'dental.prescription',
            'res_id': self.env['dental.prescription'].search([
                ('appointment_id', '=', self.id)], limit=1).id,
        }
