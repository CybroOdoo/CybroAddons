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


class PortalEmployeePayslip(CustomerPortal):
    """Display user counters"""

    def _prepare_home_portal_values(self, counters):
        """Display counters of payslips"""
        values = super()._prepare_home_portal_values(counters)
        if "payslip_count" in counters:
            values["payslip_count"] = (
                request.env["hr.payslip"]
                .sudo()
                .search_count([("employee_id.user_id", "=", request.env.user.id)])
            )
        return values


class WebsiteHrPortalPayslip(http.Controller):
    """Display current user payslips"""

    @http.route(["/my/payslip"], type="http", auth="user", website=True)
    def portal_my_payslip(self, sortby=None, search="", search_in="All"):
        """Display current user payslips"""
        searchbar_sortings = {
            "struct_id": {"label": "Structure", "order": "struct_id desc"}
        }
        searchbar_inputs = {
            "All": {
                "label": "All",
                "input": "All",
                "domain": [
                    "|",
                    "|",
                    ("name", "ilike", search),
                    ("number", "ilike", search),
                    ("struct_id", "ilike", search),
                ],
            },
            "Name": {
                "label": "Name",
                "input": "Name",
                "domain": [("name", "ilike", search)],
            },
            "Reference": {
                "label": "Reference",
                "input": "Reference",
                "domain": [("number", "ilike", search)],
            },
            "Structure": {
                "label": "Structure",
                "input": "Structure",
                "domain": [("struct_id", "ilike", search)],
            },
        }
        if not sortby:
            sortby = "struct_id"
        search_domain = searchbar_inputs[search_in]["domain"]
        payslip = (
            request.env["hr.payslip"]
            .sudo()
            .search([("employee_id.user_id", "=", request.env.user.id)])
        )
        return http.request.render(
            "website_hr_portal.portal_employee_payslips",
            {
                "payslip_id": payslip.search(search_domain),
                "searchbar_sortings": searchbar_sortings,
                "searchbar_inputs": searchbar_inputs,
                "sortby": sortby,
                "search": search,
                "search_in": search_in,
                "page_name": "payslip",
            },
        )

    @http.route(
        ["/payslip/details/<int:value>"], type="http", auth="user", website=True
    )
    def portal_payslip_details(self, value):
        """Display current user payslip details"""
        payslip = request.env["hr.payslip"].sudo().browse(value)
        payslip_details = [schedule for schedule in payslip.line_ids]
        return http.request.render(
            "website_hr_portal.payslip_portal_content",
            {
                "payslip": payslip,
                "payslip_details": payslip_details,
                "page_name": "payslip_details",
            },
        )
