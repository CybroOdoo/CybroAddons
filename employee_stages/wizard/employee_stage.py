# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import fields, models


class EmployeeStage(models.TransientModel):
    """Wizards to set the related user"""
    _name = 'employee.stage'
    _description = "Set Related User"

    related_user_id = fields.Many2one('res.users', string="Related User",
                                      help="Set related user for the employee")

    def set_as_employee(self):
        """This is used to create a related user for the employee in
        employment stage"""
        context = self._context
        employee_obj = self.env['hr.employee'].browse(
            context.get('employee_id'))
        if self.related_user_id:
            employee_obj.user_id = self.related_user_id
        employee_obj.set_as_employee()
