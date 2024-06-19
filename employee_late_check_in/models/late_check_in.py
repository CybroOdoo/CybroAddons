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
from odoo import api, fields, models


class LateCheckIn(models.Model):
    """Model to store late check-in records"""

    _name = "late.check.in"
    _description = "Late Check In"

    name = fields.Char(
        readonly=True, string="Name", help="Reference number of the record"
    )
    employee_id = fields.Many2one(
        "hr.employee", string="Employee", help="Late employee"
    )
    late_minutes = fields.Integer(
        string="Late Minutes",
        help="The field indicates the number of minutes the worker is late.",
    )
    date = fields.Date(string="Date", help="Current date")
    penalty_amount = fields.Float(
        compute="_compute_penalty_amount",
        help="Amount needs to be deducted",
        string="Amount",
    )
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("approved", "Approved"),
            ("refused", "Refused"),
            ("deducted", "Deducted"),
        ],
        string="State",
        default="draft",
        help="State of the record",
    )
    attendance_id = fields.Many2one(
        "hr.attendance", string="Attendance", help="Attendance of the employee"
    )

    @api.model
    def create(self, vals_list):
        """Create a sequence for the model"""
        vals_list["name"] = self.env["ir.sequence"].next_by_code("late.check.in") or "/"
        return super(LateCheckIn, self.sudo()).create(vals_list)

    def _compute_penalty_amount(self):
        """Compute the penalty amount if the employee was late"""
        for rec in self:
            amount = float(
                self.env["ir.config_parameter"].sudo().get_param("employee_late_check_in.deduction_amount")
            )
            rec.penalty_amount = amount
            if (
                self.env["ir.config_parameter"].sudo().get_param("employee_late_check_in.deduction_type")
                == "minutes"
            ):
                rec.penalty_amount = amount * rec.late_minutes

    def approve(self):
        """Change state to approved when approve button clicks"""
        self.state = "approved"

    def reject(self):
        """Change state refused when refuse button clicks"""
        self.state = "refused"
