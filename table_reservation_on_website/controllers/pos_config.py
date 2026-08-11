# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
###############################################################################
from odoo import http
from odoo.http import request


class ResConfigSettingsController(http.Controller):
    """Controller for retrieving POS opening and closing hours."""

    @http.route('/pos/get_opening_closing_hours', type='json', auth='public', methods=['POST'])
    def get_opening_closing_hours(self):
        """Return POS opening, closing, and reservation lead-time settings."""
        pos_config = request.env['pos.config'].sudo().search([
            ('module_pos_restaurant', '=', True),
            ('set_opening_hours', '=', True)
        ], limit=1)
        if not pos_config:
            pos_config = request.env['pos.config'].sudo().search([
                ('module_pos_restaurant', '=', True)
            ], limit=1)

        if pos_config and pos_config.set_opening_hours:
            opening_val = pos_config.opening_hour
            closing_val = pos_config.closing_hour
        else:
            opening_val = 0.0
            closing_val = 24.0

        try:
            opening_hour = self.float_to_time(float(opening_val))
            closing_hour = self.float_to_time(float(closing_val))
        except (ValueError, TypeError):
            opening_hour = "00:00"
            closing_hour = "23:59"

        is_lead_time_param = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.is_lead_time')
        is_lead_time = str(is_lead_time_param).lower() in ('true', '1') if is_lead_time_param else False
        reservation_lead_time = float(
            request.env['ir.config_parameter'].sudo().get_param(
                'table_reservation_on_website.reservation_lead_time') or 0.0)

        if pos_config:
            return {
                'opening_hour': opening_hour,
                'closing_hour': closing_hour,
                'is_lead_time': is_lead_time,
                'reservation_lead_time': reservation_lead_time
            }
        return {'error': 'POS configuration not found'}

    def float_to_time(self, hour_float):
        """ Convert float hours (e.g., 8.5 → 08:30) to HH:MM format """
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
