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
#############################################################################
from odoo import fields, models


class EmployeeStage(models.TransientModel):
    """Wizards to set the related user"""
    _name = 'employee.stage'
    _description = "Set Related User"

    related_user_id = fields.Many2one('res.users',
                                      help="Set related user for the employee")

    def set_as_employee(self):
        """This is used to create a related user for the employee in
        employment stage"""
        employee_id = self.env.context.get('active_id') or self.env.context.get('employee_id')
        employee_obj = self.env['hr.employee'].browse(employee_id)
        if self.related_user_id and employee_obj:
            employee_obj.user_id = self.related_user_id
        if employee_obj:
            employee_obj.set_as_employee()
