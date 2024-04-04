# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models, _


class HrEmployee(models.Model):
    """Inherit the model to add fields and methods"""

    _inherit = "hr.employee"

    late_check_in_count = fields.Integer(
        string="Late Check-In",
        compute="_compute_late_check_in_count",
        help="Count of employee's late checkin",
    )

    def action_to_open_late_check_in_records(self):
        """
        :return: dictionary defining the action to open the late check-in
        records window.
        :rtype: dict
        """
        return {
            "name": _("Employee Late Check-in"),
            "domain": [("employee_id", "=", self.id)],
            "res_model": "late.check.in",
            "type": "ir.actions.act_window",
            "view_mode": "tree,form",
            "limit": 80,
        }

    def _compute_late_check_in_count(self):
        """Compute the late check-in count"""
        for rec in self:
            rec.late_check_in_count = self.env["late.check.in"].search_count(
                [("employee_id", "=", rec.id)]
            )
