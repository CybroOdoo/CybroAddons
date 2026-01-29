# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Jumana Haseen (odoo@cybrosys.com)
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


class WebsiteEstimatedDeliveryTime(http.Controller):
    """Returns the estimated delivery time"""

    @http.route(['/website_estimated_delivery_time'], type='json',
                auth="public", website=True, csrf=False)
    def website_estimated_delivery_time(self, **kwargs):
        """Returns the estimated delivery time and messages"""
        data = {
            'product_base_availability': 'False',
            'website_base_availability': 'False',
            'available_message': '',
            'unavailable_message': ''
        }
        days = []
        product_id = request.env['product.template'].browse(
            int(kwargs.get('product_id'))
        )
        message = request.env['website.estimated.delivery.time'].sudo().search(
            [], limit=1
        )
        message_product = request.env[
            'product.estimated.delivery.time'].sudo().search([
            ('product_id', '=', product_id.id)
        ])

        pin_entered = kwargs.get('pin_number')

        product_pin_found = False

        if product_id.overwrite_existing_config:
            for rec in message_product:
                if rec.pin == pin_entered:
                    days.append(rec.days)
                    data['product_base_availability'] = 'True'
                    data['available_message'] = ' '.join(
                        [str(rec.available_message), str(days[0]), 'Days']
                    )
                    product_pin_found = True
                    break
            if not product_pin_found:
                data['unavailable_message'] = message_product[
                    0].unavailable_message if message_product else message.unavailable_message
        else:
            website_pin_found = False
            for rec in message.estimated_delivery_time_ids:
                if rec.pin == pin_entered:
                    days.append(rec.days)
                    data['website_base_availability'] = 'True'
                    website_pin_found = True
                    break
            if days:
                if message.display_mode == 'exact':
                    data['available_message'] = ' '.join(
                        [str(message.available_message), str(days[0]), 'Days']
                    )
                else:
                    if message.delivery_day_range == 'days_after':
                        data['available_message'] = ' '.join(
                            [str(message.available_message), str(days[0]), '-',
                             str(days[0] + message.number_of_days), 'Days']
                        )
                    else:
                        days_before = max(0, days[0] - message.number_of_days)
                        data['available_message'] = ' '.join(
                            [str(message.available_message),
                             str(days_before), '-',
                             str(days[0]), 'Days']
                        )
            if not website_pin_found:
                data['unavailable_message'] = message.unavailable_message

        # Ensure unavailable_message is set correctly if no availability found
        if data['product_base_availability'] == 'False' and data[
            'website_base_availability'] == 'False':
            data['unavailable_message'] = message.unavailable_message
        return data
