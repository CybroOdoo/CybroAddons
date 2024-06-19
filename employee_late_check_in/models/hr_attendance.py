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
import pytz
from datetime import datetime, timedelta
from odoo import fields, models


class HrAttendance(models.Model):
    """Inherit the module to add fields and methods"""

    _inherit = "hr.attendance"

    late_check_in = fields.Integer(
        string="Late Check-in(Minutes)",
        compute="_compute_late_check_in",
        help="This indicates the duration of the employee's tardiness.",
    )

    def _compute_late_check_in(self):
        """Calculate late check-in minutes for each record in the current Odoo
        model.This method iterates through the records and calculates late
        check-in minutes based on the employee's contract schedule.The
        calculation takes into account the employee's time zone, scheduled
        check-in time, and the actual check-in time."""
        for rec in self:
            rec.late_check_in = 0.0
            if rec.employee_id.contract_id:
                for schedule in (
                    rec.sudo()
                    .employee_id.contract_id.resource_calendar_id.sudo()
                    .attendance_ids
                ):
                    if (
                        schedule.dayofweek == str(rec.sudo().check_in.weekday())
                        and schedule.day_period == "morning"
                    ):
                        dt = rec.check_in
                        if self.env.user.tz in pytz.all_timezones:
                            old_tz = pytz.timezone("UTC")
                            new_tz = pytz.timezone(self.env.user.tz)
                            dt = old_tz.localize(dt).astimezone(new_tz)
                        str_time = dt.strftime("%H:%M")
                        check_in_date = datetime.strptime(str_time, "%H:%M").time()
                        start_date = datetime.strptime(
                            "{0:02.0f}:{1:02.0f}".format(
                                *divmod(schedule.hour_from * 60, 60)
                            ),
                            "%H:%M",
                        ).time()
                        check_in = timedelta(
                            hours=check_in_date.hour, minutes=check_in_date.minute
                        )
                        start_date = timedelta(
                            hours=start_date.hour, minutes=start_date.minute
                        )
                        if check_in > start_date:
                            final = check_in - start_date
                            rec.sudo().late_check_in = final.total_seconds() / 60

    def late_check_in_records(self):
        """Function creates records in late.check.in model for the employees
        who were late as a scheduled action"""
        minutes_after = (
            int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("employee_late_check_in.late_check_in_after")
            )
            or 0
        )
        max_limit = (
            int(
                self.env["ir.config_parameter"]
                .sudo()
                .get_param("employee_late_check_in.maximum_minutes")
            )
            or 0
        )
        for rec in self.sudo().search(
            [
                (
                    "id",
                    "not in",
                    self.env["late.check.in"].sudo().search([]).attendance_id.ids,
                )
            ]
        ):
            late_check_in = rec.sudo().late_check_in + 210
            if (
                rec.late_check_in > minutes_after
                and late_check_in > minutes_after
                and late_check_in < max_limit
            ):
                self.env["late.check.in"].sudo().create(
                    {
                        "employee_id": rec.employee_id.id,
                        "late_minutes": late_check_in,
                        "date": rec.check_in.date(),
                        "attendance_id": rec.id,
                    }
                )
