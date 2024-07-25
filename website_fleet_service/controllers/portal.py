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
from odoo.addons.portal.controllers import portal


class CustomerPortal(portal.CustomerPortal):
    """Class to count total number of service created"""

    def _prepare_home_portal_values(self, counters):
        """Function to add total service created by the current user"""
        values = super()._prepare_home_portal_values(counters)
        if "contact_count" in counters:
            values["contact_count"] = (
                request.env["service.booking"]
                .sudo()
                .search_count(
                    [("partner_id.id", "=", request.env.user.commercial_partner_id.id)]
                )
            )
        return values

    @http.route(["/service_portal"], type="http", auth="public", website=True)
    def car_service_portal(self):
        """function to create the tree view car service"""
        service_booking = (
            request.env["service.booking"]
            .sudo()
            .search([("partner_id.id", "=", request.env.user.commercial_partner_id.id)])
        )
        return request.render(
            "website_fleet_service.portal_car_service",
            {"car_service_portal": service_booking, "page_name": "car_service_booking"},
        )

    @http.route(
        ['/service_portal/<model("service.booking"):contract>'],
        type="http",
        auth="public",
        website=True,
    )
    def service_portal(self, contract):
        """function to add form view of the car service"""
        car_service_ids = request.env["service.booking"].sudo().browse(contract.id)
        service_worksheet_ids = (
            request.env["service.worksheet"]
            .sudo()
            .search([("service_booking_id", "=", contract.id)])
        )
        return http.request.render(
            "website_fleet_service.portal_car_service_details",
            {
                "car_service_ids": car_service_ids,
                "service_worksheet_ids": service_worksheet_ids,
                "page_name": "service_portal",
            },
        )
