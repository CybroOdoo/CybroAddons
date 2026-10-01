# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class DashboardTodo(models.Model):
    """Model representing individual to-do items inside a dashboard card."""
    _name = "dashboard.todo"
    _description = "Dashboard Todo"

    name = fields.Char(string="Todo Name", help="Name of the todo.", required=True)
    card_id = fields.Many2one(
        comodel_name="dashboard.card",
        string="Card",
        help="Card to which this todo belongs."
    )
    status = fields.Selection(
        selection=[
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
            ("complete", "Complete"),
            ("ongoing", "Ongoing")
        ],
        string="Status",
        help="Current status of the todo."
    )
    is_done = fields.Boolean(
        string="Is Done",
        help="Check if the todo is completed."
    )
    priority_backup = fields.Selection(
        selection=[
            ("high", "High"),
            ("medium", "Medium"),
            ("low", "Low"),
            ("ongoing", "Ongoing")
        ],
        string="Previous Priority",
        help="Backup of previous priority level."
    )
