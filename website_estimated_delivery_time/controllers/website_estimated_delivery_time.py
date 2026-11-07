# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Surya Gayathry TA (odoo@cybrosys.com)
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
###############################################################################
from odoo import http
from odoo.http import request


class WebsiteEstimatedDeliveryTime(http.Controller):
    """ Returns the estimated delivery time """

    @staticmethod
    def _format_available_message(settings, days):
        """Build the delivery message from the configured display mode."""
        available_message = (
            settings.available_message
            if settings else 'This Product Will Be Delivered Within'
        )
        display_mode = settings.display_mode if settings else 'exact'
        delivery_day_range = (
            settings.delivery_day_range if settings else 'days_after'
        )
        number_of_days = settings.number_of_days if settings else 0

        if display_mode == 'exact':
            return ' '.join([str(available_message), str(days), 'Days'])
        if delivery_day_range == 'days_after':
            return ' '.join([
                str(available_message), str(days), '-',
                str(days + number_of_days), 'Days',
            ])
        days_before = max(days - number_of_days, 0)
        return ' '.join([
            str(available_message), str(days_before), '-', str(days), 'Days',
        ])

    @http.route(['/website_estimated_delivery_time'], type='jsonrpc',
                auth="public", website=True, csrf=False)
    def website_estimated_delivery_time(self, **kwargs):
        """ Returns the estimated delivery time and messages """
        data = {'product_base_availability': 'False',
                'website_base_availability': 'False',
                'available_message': '', 'unavailable_message': ''}
        product_template_id = 0
        try:
            product_template_id = int(kwargs.get('product_template_id') or 0)
        except (TypeError, ValueError):
            product_template_id = 0
        try:
            product_id = int(kwargs.get('product_id') or 0)
        except (TypeError, ValueError):
            product_id = 0
        pin_number = (kwargs.get('pin_number') or '').strip()

        settings = request.env['website.estimated.delivery.time'].sudo().search(
            [], limit=1)
        if settings:
            data['unavailable_message'] = settings.unavailable_message
        else:
            data['unavailable_message'] = (
                'This Product Is Not Available In Your Location'
            )

        if not (product_template_id or product_id) or not pin_number:
            return data

        product = request.env['product.template'].sudo().browse(product_template_id)
        if not product.exists() and product_id:
            product = request.env['product.product'].sudo().browse(
                product_id
            ).product_tmpl_id
        if not product.exists():
            return data

        if product.overwrite_existing_config:
            matching_record = product.product_estimated_delivery_time_ids.filtered(
                lambda record: (record.pin or '').strip() == pin_number
            )[:1]
            if matching_record:
                data['product_base_availability'] = 'True'
                available_message = (
                    settings.available_message
                    if settings else 'This Product Will Be Delivered Within'
                )
                data['available_message'] = ' '.join([
                    str(available_message), str(matching_record.days), 'Days',
                ])
        else:
            matching_record = settings.estimated_delivery_time_ids.filtered(
                lambda record: record.display_mode == settings.display_mode
                and (record.pin or '').strip() == pin_number
            )[:1]
            if matching_record:
                data['website_base_availability'] = 'True'
                data['available_message'] = self._format_available_message(
                    settings, matching_record.days
                )
        return data
