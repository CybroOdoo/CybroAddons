# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    """To create dental appointments"""
    _name = "dental.appointment"
    _description = "Dental Appointment"
    _inherit = "mail.thread"
    _rec_name = 'sequence_no'

    sequence_no = fields.Char(string='Sequence No', readonly=True,
                              default=lambda self: _('New'),
                              copy=False,
                              help="Sequence number of appointment")
    token_no = fields.Integer(string="Token No", readonly=True,
                              help="Token number for the appointment")
    patient_id = fields.Many2one('res.partner', string="Patient",
                                 required=True,
                                 help="Add the patient")
    patient_phone = fields.Char(related="patient_id.phone", string="Phone",
                                help="Phone number of the patient")
    patient_age = fields.Integer(related="patient_id.patient_age", string="Age",
                                 help="Age of the patient")
    specialist_id = fields.Many2one('dental.specialist',
                                    string="Doctors Department",
                                    required=True,
                                    help="Doctors Department")
    doctor_id = fields.Many2one('hr.employee', string="Doctor",
                                required=True,
                                domain="[('id', 'in', doctor_ids)]",
                                help="Name the of the doctor")
    doctor_ids = fields.Many2many('hr.employee',
                                  compute='_compute_doctor_ids',
                                  compute_sudo=True,
                                  string="Doctors Data", help="Doctors Data")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      compute='_compute_time_shifts',
                                      string="Shifts", help="Doctor shifts")
    shift_id = fields.Many2one('dental.time.shift', string="Shift",
                               required=True,
                               domain="[('id', 'in', time_shift_ids)]",
                               help="Name of the shift")
    date = fields.Date(string="Date", required=True,
                       help="Date of the appointment")
    reason = fields.Text(string="Reason", help="Reason for appointment")
    state = fields.Selection([('draft', 'Draft'),
                              ('new', 'New'),
                              ('pending', 'Pending'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')],
                             default='draft',
                              string="Status", help="Status of appointment")

    @api.onchange('specialist_id')
    def _onchange_specialist_id(self):
        """To clear doctor field while changing specialist"""
        self.doctor_id = False

    @api.onchange('doctor_id')
    def _onchange_doctor_id(self):
        """To clear shift field while changing doctor"""
        self.shift_id = False

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

    @api.model_create_multi
    def create(self, vals_list):
        """Generating sequence number and token number for the appointment"""
        recorded_tokens = {}
        for vals in vals_list:
            if not vals.get('sequence_no') or vals.get('sequence_no') == _('New'):
                vals['sequence_no'] = self.env['ir.sequence'].next_by_code(
                    'dental.appointment') or _('New')
            doctor_id = vals.get('doctor_id')
            date = vals.get('date')
            shift_id = vals.get('shift_id')
            if doctor_id and date and shift_id:
                try:
                    d_id = int(doctor_id)
                    s_id = int(shift_id)
                except (ValueError, TypeError):
                    d_id = doctor_id
                    s_id = shift_id
                key = (d_id, date, s_id)
                if key not in recorded_tokens:
                    last_token = self.search([
                        ('doctor_id', '=', d_id),
                        ('date', '=', date),
                        ('shift_id', '=', s_id)
                    ], order='id desc', limit=1)
                    recorded_tokens[key] = last_token.token_no if last_token else 0
                recorded_tokens[key] += 1
                vals['token_no'] = recorded_tokens[key]
            if vals.get('state', 'draft') == 'draft':
                vals['state'] = 'new'
        return super(DentalAppointment, self).create(vals_list)

    def action_cancel(self):
        """Cancel appointment"""
        self.state = 'cancel'

    def action_create_appointment(self):
        """Update draft to new"""
        self.state = 'new'

    def action_prescription(self):
        """To view medicine prescriptions from appointment"""
        return {
            'name': _('Prescription'),
            'view_mode': 'list,form',
            'res_model': 'dental.prescription',
            'type': 'ir.actions.act_window',
            'domain': [('appointment_id', '=', self.id)],
            'context': {'default_appointment_id': self.id,
                        'default_patient_id': self.patient_id.id,
                        'default_doctor_id': self.doctor_id.id}
        }
