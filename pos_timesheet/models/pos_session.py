# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohammed Hisam (odoo@cybrosysy.com)
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
from odoo import api, fields, models, _


class PosSession(models.Model):
    """Inherits the PosSession class for adding fields and functions"""

    _inherit = "pos.session"

    task_id = fields.Many2one(
        "project.task",
        string="Task",
        help="Session Timesheet Task",
        ondelete="cascade",
        default=False,
    )

    @api.model_create_multi
    def create(self, vals_list):
        """Create Task for add timesheet"""
        result = super().create(vals_list)

        if result.config_id.module_pos_hr and result.config_id.time_log:
            result.task_id = self.env["project.task"].create(
                {
                    "name": result.name,
                    "project_id": result.config_id.project_id.id,
                    "company_id": result.config_id.company_id.id,
                }
            )
        return result

    def _pos_ui_models_to_load(self):
        """loads models to the UI"""
        result = super()._pos_ui_models_to_load()
        result.append("account.analytic.line")
        return result

    def _loader_params_account_analytic_line(self):
        """Returns loader params for account"""
        return {
            "search_params": {
                "domain": [
                    ("task_id", "=", self.task_id.id),
                    ("date", "=", fields.Date.context_today(self)),
                ],
                "fields": ["employee_id", "unit_amount"],
            },
        }

    def _get_pos_ui_account_analytic_line(self, params):
        """Returns the account analytics line for the pos"""
        return (
            self.env["account.analytic.line"]
            .sudo()
            .search_read(**params["search_params"])
        )

    def _loader_params_pos_session(self):
        """Loading parameters to the session"""
        result = super()._loader_params_pos_session()
        result["search_params"]["fields"].append("task_id")
        return result

    def set_timesheet(self, data):
        """Update Timesheet of the employee"""
        for timesheet in data:
            if timesheet["workMinutes"] > 0:
                hours = timesheet["workMinutes"] / 60
                session_id = self.browse(timesheet["sessionId"])
                timestamp_seconds = timesheet["checkInTime"] / 1000
                date_time = fields.datetime.fromtimestamp(timestamp_seconds)
                date_only = date_time.date()
                sudo_timesheet = self.env["account.analytic.line"].sudo()
                employee_timesheet = sudo_timesheet.search(
                    [
                        ("task_id", "=", session_id.task_id.id),
                        ("date", "=", date_only),
                        ("employee_id", "=", timesheet["cashierId"]),
                    ],
                    limit=1,
                )
                if employee_timesheet:
                    employee_timesheet.unit_amount += hours
                else:
                    sudo_timesheet.create(
                        {
                            "task_id": session_id.task_id.id,
                            "employee_id": timesheet["cashierId"],
                            "name": session_id.name,
                            "date": date_only,
                            "unit_amount": hours,
                        }
                    )
        return True

    def action_show_time_log(self):
        """Show the task its contained timesheet for the session"""
        return {
            "name": _("Time Log"),
            "type": "ir.actions.act_window",
            "res_model": "project.task",
            "view_mode": "form",
            "res_id": self.task_id.id,
        }
