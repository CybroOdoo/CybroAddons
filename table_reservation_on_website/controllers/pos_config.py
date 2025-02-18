from datetime import datetime

from odoo import http
from odoo.http import request, _logger


class ResConfigSettingsController(http.Controller):

    @http.route('/pos/get_opening_closing_hours', type='json', auth='public', methods=['POST'])
    def get_opening_closing_hours(self):
        res_config = request.env['res.config.settings'].sudo().search([], limit=1)
        # Ensure proper time format
        try:
            opening_hour = self.float_to_time(float(res_config.pos_opening_hour))
            closing_hour = self.float_to_time(float(res_config.pos_closing_hour))
        except ValueError:
            opening_hour = "00:00"
            closing_hour = "23:59"

        if res_config:
            return {
                'opening_hour': opening_hour,
                'closing_hour': closing_hour
            }
        return {'error': 'POS configuration not found'}

    def float_to_time(self, hour_float):
        """ Convert float hours (e.g., 8.5 → 08:30) to HH:MM format """
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
