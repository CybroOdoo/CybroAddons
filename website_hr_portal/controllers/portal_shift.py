# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal


class PortalEmployeeShifts(CustomerPortal):
    """Display user counters"""

    def _prepare_home_portal_values(self, counters):
        """Display counters of shifts of current user"""
        values = super()._prepare_home_portal_values(counters)
        if "shift_count" in counters:
            values["shift_count"] = (
                request.env["hr.employee"]
                .sudo()
                .search_count([("user_id", "=", request.env.user.id)])
            )
        return values

    @http.route(["/my/shift"], type="http", auth="user", website=True)
    def portal_my_shifts(self):
        """Display current user shifts"""
        shift = (
            request.env["hr.employee"]
            .sudo()
            .search([("user_id", "=", request.env.user.id)])
        )
        leave = (
            request.env["hr.leave"].sudo().search([("id", "=", request.env.user.id)])
        )
        attendance_list = [
            schedule for schedule in shift.resource_calendar_id.attendance_ids
        ]
        data = [
            {
                "resource_calendar_id": shift.resource_calendar_id.name,
                "leave_ids": leave.number_of_days,
            }
            for shift in shift
        ]
        return http.request.render(
            "website_hr_portal.portal_employee_shifts",
            {
                "shift_id": shift,
                "data": data,
                "attendance_list": attendance_list,
                "page_name": "shifts",
            },
        )
