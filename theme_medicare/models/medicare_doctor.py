# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""Model for Medicare Doctors."""

from odoo import models, fields, api

class MedicareDoctor(models.Model):
    """Model class for managing doctor profiles."""
    _name = 'medicare.doctor'
    _description = 'Medicare Doctor'

    name = fields.Char(string='Doctor Name', required=True)
    employee_id = fields.Many2one('hr.employee', string='Related Employee')
    image = fields.Image(string='Photo')
    specialization = fields.Char(string='Specialization')
    department_id = fields.Many2one('medicare.department', string='Department')
    biography = fields.Text(string='Biography')
    active = fields.Boolean(default=True)

    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        """Auto-populate doctor name and photo when an employee is selected."""
        if self.employee_id:
            if not self.name or self.name == 'New':
                self.name = self.employee_id.name
            if not self.image and self.employee_id.image_1920:
                self.image = self.employee_id.image_1920

