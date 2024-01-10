# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sruthi Pavithran (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models


class MrpProduction(models.Model):
    """Adding fields to mrp production"""

    _inherit = "mrp.production"

    cost_per_hour = fields.Float(
        compute="_compute_cost_per_hour",
        store=True,
        string="Cost per hour",
        help="Cost per hour of production",
    )
    cost = fields.Float(
        related="cost_per_hour", store=True, string="Cost", help="Cost of production"
    )

    @api.depends("workorder_ids", "workorder_ids.duration")
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
                            "employee_id.id"
                        )
                    )
                if logged_in_user in work_center_employees:
                    cost_per = (
                        record.env["hr.employee"].browse(logged_in_user).hour_per_cost
                        * work_order.duration
                    )
                    cost.append(cost_per)
                record.cost_per_hour = sum(cost)
