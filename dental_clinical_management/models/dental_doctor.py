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
from odoo import api, fields, models
from odoo.exceptions import ValidationError



class DentalDoctor(models.Model):
    """To add the doctors of the clinic"""
    _inherit = 'hr.employee'

    job_position = fields.Char(string="Designation",
                               help="To add the job position of the doctor")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        help="Add the doctor specialised", required="1")
    dob = fields.Date(string="Date of Birth",
                      required=True,
                      help="DOB of the patient")
    doctor_age = fields.Integer(compute='_compute_doctor_age',
                                store=True,
                                string="Age",
                                help="Age of the Doctor")
    sex = fields.Selection([('male', 'Male'),
                            ('female', 'Female')],
                           string="Sex",
                           help="Sex of the patient")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift",
                                      help="Time shift of the doctor")

    @api.constrains('specialised_in_id')
    def _check_shift(self):
        for record in self:
            if record.specialised_in_id and not record.time_shift_ids:
                raise ValidationError("At least one shift must be assigned to the doctor.")


    @api.model
    def create(self, vals_list):
        res = super(DentalDoctor, self).create(vals_list)
        self.env['res.partner'].create({
            'name': vals_list['name'],
            'email': vals_list['work_email'],
            'phone': vals_list['work_phone'],
        })
        return res

    def unlink(self):
        """Delete the corresponding user from 'res.users' while
        deleting the doctor"""
        for record in self:
            self.env['res.users'].search([
                ('id', '=', record.user_id.id)]).unlink()
        res = super(DentalDoctor, self).unlink()
        return res

    @api.depends('dob')
    def _compute_doctor_age(self):
        """To calculate the age of the doctor from the DOB"""
        for record in self:
            record.doctor_age = (fields.date.today().year - record.dob.year -
                                 ((fields.date.today().month,
                                   fields.date.today().day) <
                                  (record.dob.month,
                                   record.dob.day))) if record.dob else False
