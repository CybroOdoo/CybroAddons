# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
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
from odoo import fields, models


class CostPerEmployee(models.Model):
    """Creating new models for storing cost per employee"""
    _name = 'cost.per.employee'
    _description = "Storing cost per hour of employee"

    employee_id = fields.Many2one('hr.employee',
                                  help="Select Employees",
                                  string="Employee Name")
    cost = fields.Float(related="employee_id.hour_per_cost",
                        help="Hourly cost of employee",
                        string="Cost")
    mrp_workcenter_id = fields.Many2one('mrp.workcenter',
                                        string="Work Center",
                                        help="Select work centers")
