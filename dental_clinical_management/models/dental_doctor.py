# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Gayathri V(<https://www.cybrosys.com>)
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


class DentalDoctor(models.Model):
    """To add the doctors of the clinic"""
    _inherit = 'hr.employee'

    job_position = fields.Char(string="Designation",
                               help="To add the job position of the doctor")
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        help="Add the doctor specialised")
    dob = fields.Date(string="Date of Birth", required=True, help="DOB of "
                                                                  "the patient")
    doctor_age = fields.Integer(compute='_compute_doctor_age', store=True,
                                string="Age", help="Age of the patient")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              string="Gender", help="Gender of the patient")
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift", help="Time shift of "
                                                                "the doctor")

    def unlink(self):
        """Delete the corresponding user from res.users while
        deleting the doctor"""
        for record in self:
            self.env['res.users'].browse(record.user_id.id).unlink()
        return super(DentalDoctor, self).unlink()

    @api.depends('dob')
    def _compute_doctor_age(self):
        """To calculate the age of the doctor from the DOB"""
        for record in self:
            record.doctor_age = (fields.date.today().year - record.dob.year -
                                 ((fields.date.today().month,
                                   fields.date.today().day) <
                                  (record.dob.month,
                                   record.dob.day))) if record.dob else False


class EmployeePublic(models.Model):
    _inherit = 'hr.employee.public'

    job_position = fields.Char(string="Designation", readonly=True)
    specialised_in_id = fields.Many2one('dental.specialist',
                                        string='Specialised In',
                                        readonly=True)
    dob = fields.Date(string="Date of Birth", required=True, readonly=True)
    doctor_age = fields.Integer(string="Age", readonly=True)
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
                              string="Gender", readonly=True)
    time_shift_ids = fields.Many2many('dental.time.shift',
                                      string="Time Shift", readonly=True)
