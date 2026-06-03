# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import http
from odoo.http import request
import time


class DashboardCarousel(http.Controller):
    """Dashboard view"""
    @http.route('/get_dashboard_carousel', auth="public", type='json')
    def get_dashboard_carousel(self):
        """This function the showing the insta post as carousel"""
        records = request.env['insta.post'].sudo().search([])
        if not records:
            return ""

        events_per_slide = 3
        records_grouped = []
        record_list = []
        for index, record in enumerate(records, 1):
            record_list.append(record)
            if index % events_per_slide == 0:
                records_grouped.append(record_list)
                record_list = []
        if record_list:
            records_grouped.append(record_list)

        values = {
            "objects": records_grouped,
            "events_per_slide": events_per_slide,
            "num_slides": len(records_grouped),
            "uniqueId": "pc-%d" % int(time.time() * 1000),
        }
        response = http.Response(
            template='insta_feed_snippet.s_carousel_template_items', qcontext=values)
        return response.render()
