# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Raneesha MK (odoo@cybrosys.com)
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
################################################################################
from odoo import http
from odoo.http import request


class WebsiteFleetService(http.Controller):
    """class to add car service booking menu in website"""

    @http.route("/service_booking", type="http", auth="public", website=True)
    def service_booking(self):
        """function to render car service booking values to XML"""
        vehicle_ids = (
            request.env["fleet.vehicle.model"]
            .sudo()
            .search([("vehicle_type", "=", "car")])
        )
        service_type_ids = request.env["service.package"].sudo().search([])
        return http.request.render(
            "website_fleet_service.car_service_booking_page",
            {"vehicle_ids": vehicle_ids, "service_type_ids": service_type_ids},
        )

    @http.route("/service_booking/submit", type="http", auth="public", website=True)
    def success_page(self, **post):
        """function to create booking and return to success page"""
        booking_id = (
            request.env["service.booking"]
            .sudo()
            .create({
                "partner_id": request.env.user.partner_id.id,
                "model_id": post.get("vehicle_model"),
                "vehicle_no": post.get("vehicle_no"),
                "service_package_id": post.get("service_type"),
                "date": post.get("date"),
                "location": post.get("location"),
                "number": post.get("number"),
                "special_instruction": post.get("instruction"),
            })
        )
        return request.render(
            "website_fleet_service.car_service_booking_success_page",
            {"booking_id": booking_id},
        )

    @http.route("/service_package", type="http", auth="public", website=True)
    def service_package_details(self):
        """function to render values to XML"""
        service_package_ids = request.env["service.package"].sudo().search([])
        service_line_ids = request.env["service.line"].sudo().search([])
        return http.request.render(
            "website_fleet_service.service_package_page",
            {
                "service_package_ids": service_package_ids,
                "service_line_ids": service_line_ids,
            },
        )
