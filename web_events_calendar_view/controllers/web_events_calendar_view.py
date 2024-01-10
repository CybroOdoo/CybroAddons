# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Renu M (odoo@cybrosys.info)
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
from datetime import date, timedelta
from odoo import http
from odoo.fields import Date
from odoo.http import request


class EventCalendar(http.Controller):
    @http.route("/web_events_calendar_view/days_with_events",
                auth="public", type="json", website=True)
    def days_with_events(self, start, end):
        """Day with any events.

        start:
            Search events from that date.

        end:
            Search events until that date.
        """
        events = request.env["event.event"].search([
            "|",
            ("date_begin", "<=", end),
            ("date_end", ">=", start),
        ])
        days = set()
        one_day = timedelta(days=1)
        start = Date.from_string(start)
        end = Date.from_string(end)
        for event in events:
            now = max(Date.from_string(event.date_begin), start)
            event_end = min(Date.from_string(event.date_end), end)
            while now <= event_end:
                days.add(now)
                now += one_day
        return [Date.to_string(day) for day in days]

    @http.route("/web_events_calendar_view/events_for_day",
                auth="public", type="json", website=True)
    def events_for_day(self, day=None, limit=None):
        """Day wise list of events.

        day:
            Date in a string. If ``None``, we'll search for upcoming events
            from today up to specified limit.

        limit:
            How many results to return.
        """
        ref = day or Date.to_string(date.today())
        domain = [
            ("date_end", ">=", ref),
        ]
        if day:
            domain.append(("date_begin", "<=", ref))
        return request.env["event.event"].search_read(
            domain=domain,
            limit=limit,
            fields=[
                "date_begin_pred_located",
                "name",
                "event_type_id",
                "website_published",
                "website_url",
            ],
        )

    @http.route(['/calendar_events'], type='http', auth="public",
                website=True)
    def calendar_events(self):
        return request.render(
            "web_events_calendar_view.global_events_calendar")
