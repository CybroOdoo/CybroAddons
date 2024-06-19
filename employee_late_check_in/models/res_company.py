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
from odoo import fields, models


class ResCompany(models.Model):
    """Inherit the model to add fields"""

    _inherit = "res.company"

    deduction_amount = fields.Float(
        help="How much amount need to be deducted if a employee was late",
        string="Deduction Amount",
    )
    currency_id = fields.Many2one(
        "res.currency", default=lambda self: self.env.company.currency_id.id
    )
    maximum_minutes = fields.Char(
        help="Maximum time limit a employee was considered as late",
        string="Maximum Late Minute",
    )
    late_check_in_after = fields.Char(
        help="When should the late check-in count down starts.",
        string="Late Check-in Starts After",
    )
    deduction_type = fields.Selection(
        selection=[("minutes", "Per Minutes"), ("total", "Per Total")],
        default="minutes",
        string="Deduction Type",
        help="Type of deduction, (If Per Minutes is chosen then for each "
        "minutes given amount is deducted, if Per Total is chosen then "
        "given amount is deducted from the total salary)",
    )
