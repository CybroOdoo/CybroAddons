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
from odoo import api, fields, models


class MrpProduction(models.Model):
    """Adding fields to mrp production"""
    _inherit = 'mrp.production'

    cost_per_hour = fields.Float(compute='_compute_cost_per_hour', store=True,
                                 string="Cost per hour",
                                 help="Cost per hour of production")
    cost = fields.Float(related='cost_per_hour', store=True, string="Cost",
                        help="Cost of production")

    @api.depends('workorder_ids', 'workorder_ids.duration')
    def _compute_cost_per_hour(self):
        """Calculate cost per hour of employee"""
        for record in self:
            logged_in_user = record.env.user.employee_id.id
            record.cost_per_hour = 0
            cost = []
            if record.workorder_ids:
                for work_order in record.workorder_ids:
                    work_center_employees = (
                        work_order.workcenter_id.cost_per_employee_ids.mapped(
                            'employee_id.id'))
                if logged_in_user in work_center_employees:
                    cost_per = record.env['hr.employee'].browse(
                        logged_in_user).hour_per_cost * work_order.duration
                    cost.append(cost_per)
                record.cost_per_hour = sum(cost)
