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


class PortalEmployeeEvents(CustomerPortal):
    """Display user counters"""

    def _prepare_home_portal_values(self, counters):
        """Display counters of events of current user"""
        values = super()._prepare_home_portal_values(counters)
        if "event_count" in counters:
            values["event_count"] = request.env["event.event"].sudo().search_count([])
        return values


class WebsiteHrPortalEvents(http.Controller):
    """Display current user events"""

    @http.route(["/my/event"], type="http", auth="user", website=True)
    def portal_my_events(self, sortby=None, search="", search_in="All"):
        """Display current user events"""
        searchbar_sortings = {
            "name": {"label": "Name", "order": "name"},
            "date_end": {"label": "Date", "order": "date_end desc"},
            "event_type_id": {"label": "Event Type", "order": "event_type_id"},
            "address_id": {"label": "Venue", "order": "address_id"},
        }
        searchbar_inputs = {
            "All": {
                "label": "All",
                "input": "All",
                "domain": [
                    "|",
                    "|",
                    ("event_type_id", "ilike", search),
                    ("name", "ilike", search),
                    ("address_id", "ilike", search),
                ],
            },
            "Event Type": {
                "label": "Event Type",
                "input": "Event Type",
                "domain": [("event_type_id", "ilike", search)],
            },
            "Name": {
                "label": "Name",
                "input": "Name",
                "domain": [("name", "ilike", search)],
            },
            "Venue": {
                "label": "Venue",
                "input": "Venue",
                "domain": [("address_id", "ilike", search)],
            },
        }
        if not sortby:
            sortby = "event_type_id"
        order = searchbar_sortings[sortby]["order"]
        search_domain = searchbar_inputs[search_in]["domain"]
        event = request.env["event.event"].sudo().search(search_domain, order=order)
        return http.request.render(
            "website_hr_portal.portal_employee_events",
            {
                "event": event,
                "searchbar_sortings": searchbar_sortings,
                "sortby": sortby,
                "search": search,
                "search_in": search_in,
                "searchbar_inputs": searchbar_inputs,
                "page_name": "events",
            },
        )
