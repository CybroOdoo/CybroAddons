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


class DentalTimeShift(models.Model):
    """Doctors time shift, different time slots"""
    _name = 'dental.time.shift'
    _description = "Dental Time Shift"
    _rec_name = 'name'

    name = fields.Char(string='Name', readonly=True,
                       help="name of the time shifts")
    shift_type = fields.Selection(
        selection=[('morning', 'Morning'), ('day', 'Day'),
                   ('evening', 'Evening'), ('night', 'Night')],
        string="Shift Type", help="Selection field for the shift type")
    start_time = fields.Float(string="Start Time", help="start time of time slot")
    end_time = fields.Float(string="End Time", help="End time of time slot")

    @api.model_create_multi
    def create(self, vals_list):
        """Overrides the default create method to set the `name` field of the
        newly created `dental.time.shift` record(s) to a string that represents
        the shift time range."""
        res = super(DentalTimeShift, self).create(vals_list)
        res.name = f'{res.start_time} to {res.end_time}'
        return res

    @api.onchange('start_time', 'end_time')
    def _onchange_time(self):
        name = f'{self.start_time} to {self.end_time}'
        self.update({'name': name})

