# -*- coding: utf-8 -*-
###################################################################################
#    A part of OpenHrms Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo.exceptions import ValidationError
from odoo import models, fields, api


class HrEmployeeShift(models.Model):
    _inherit = 'resource.calendar'

    color = fields.Integer(string='Color Index')
    hr_department = fields.Many2one('hr.department', string="Department", required=True)
    sequence = fields.Integer(string="Sequence", required=True, default=1)

    @api.constrains('sequence')
    def validate_seq(self):
        record = self.env['resource.calendar'].search([('hr_department', '=', self.hr_department.id),
                                                       ('sequence', '=', self.sequence)
                                                       ])
        if len(record) > 1:
            raise ValidationError("One record with same sequence is already active."
                                  "You can't activate more than one record  at a time")
