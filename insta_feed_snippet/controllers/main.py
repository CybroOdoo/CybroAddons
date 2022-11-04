from odoo import http
from odoo.http import request
import time


class DashbaordCarousel(http.Controller):
    @http.route('/get_dashbaord_carousel', auth="public", type='json')
    def get_dashbaord_carousel(self):
        events_per_slide = 3
        records = request.env['insta.post'].sudo().search(
            [])
        records_grouped = []
        record_list = []
        for index, record in enumerate(records, 1):
            record_list.append(record)
            if index % events_per_slide == 0:
                records_grouped.append(record_list)
                record_list = []
        if any(record_list):
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
