# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
from datetime import date, timedelta
from odoo import http
from odoo.fields import Date
from odoo.http import request

class EventCalendar(http.Controller):
    """Website event calendar controller."""
    @http.route("/web_events_calendar_view/days_with_events", auth="public", type="json", website=True)
    def days_with_events(self, start, end):
        """
       Return all dates that contain at least one event within
       the specified date range.

       :param str start: Start date in YYYY-MM-DD format.
       :param str end: End date in YYYY-MM-DD format.
       :return: List of dates containing events.
       :rtype: list[str]
       """
        events = request.env["event.event"].search([
            "|",
            ("date_begin", "<=", end),
            ("date_end", ">=", start),
        ])
        days = set()
        one_day = timedelta(days=1)
        start_date = Date.from_string(start)
        end_date = Date.from_string(end)
        for event in events:
            now = max(Date.from_string(event.date_begin), start_date)
            event_end = min(Date.from_string(event.date_end), end_date)
            while now <= event_end:
                days.add(now)
                now += one_day
        return [Date.to_string(day) for day in days]

    @http.route("/web_events_calendar_view/events_for_day", auth="public", type="json", website=True)
    def events_for_day(self, day=None, limit=None):
        """Retrieve events available for a specific day or upcoming events.

        :param str day: Date in YYYY-MM-DD format.
        :param int limit: Maximum number of records to return.
        :return: Event details for the requested day.
        :rtype: list[dict]"""
        ref = day or Date.to_string(date.today())
        domain = [("date_end", ">=", ref)]
        if day:
            domain.append(("date_begin", "<=", ref))
        return request.env["event.event"].search_read(
            domain=domain,
            limit=limit,
            fields=["date_begin_pred_located", "name", "event_type_id", "website_published", "website_url"],
        )

    @http.route('/web_events_calendar_view/events', auth='public', type='json', website=True)
    def get_events(self):
        """Return upcoming events formatted for calendar display.

        :return: List of calendar event dictionaries.
        :rtype: list[dict]"""
        ref = Date.to_string(date.today())
        events = request.env['event.event'].sudo().search([("date_begin", ">=", ref)])
        event_data = []
        for event in events:
            event_dict = {
                'title': event.name,
                'start': event.date_begin.strftime('%Y-%m-%d'),
                'display': 'background'
            }
            if event.date_end:
                event_dict['end'] = event.date_end.strftime('%Y-%m-%d')
            event_data.append(event_dict)
        return event_data

    @http.route(['/calendar_events'], type='http', auth="public", website=True)
    def calendar_events(self):
        """Render the global events calendar page.

        :return: Rendered website page containing the event calendar."""
        return request.render("web_events_calendar_view.global_events_calendar")