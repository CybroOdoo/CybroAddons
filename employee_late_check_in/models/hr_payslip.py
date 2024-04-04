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


class PayslipLateCheckIn(models.Model):
    """Inherit the model to add fields and functions"""

    _inherit = "hr.payslip"

    late_check_in_ids = fields.Many2many(
        "late.check.in",
        string="Late Check-in",
        help="Late check-in records of the employee",
    )

    @api.model
    def get_inputs(self, contracts, date_from, date_to):
        """Function used for writing late check-in record in the payslip input
        tree."""
        res = super(PayslipLateCheckIn, self).get_inputs(contracts, date_to, date_from)
        late_check_in_type = self.env.ref("employee_late_check_in.late_check_in")
        late_check_in_id = self.env["late.check.in"].search(
            [
                ("employee_id", "=", self.employee_id.id),
                ("date", "<=", self.date_to),
                ("date", ">=", self.date_from),
                ("state", "=", "approved"),
            ]
        )
        if late_check_in_id:
            self.late_check_in_ids = late_check_in_id
            input_data = {
                "name": late_check_in_type.name,
                "code": late_check_in_type.code,
                "amount": sum(late_check_in_id.mapped("penalty_amount")),
                "contract_id": self.contract_id.id,
            }
            res.append(input_data)
        return res

    def action_payslip_done(self):
        """Function used for marking deducted Late check-in request."""
        for rec in self.late_check_in_ids:
            rec.state = "deducted"
        return super(PayslipLateCheckIn, self).action_payslip_done()
