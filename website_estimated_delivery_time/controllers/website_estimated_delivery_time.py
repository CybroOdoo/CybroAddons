# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ammu Raj (odoo@cybrosys.com)
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
    """Returns the estimated delivery time"""

    @http.route(['/website_estimated_delivery_time'], type='json',
                auth="public", website=True, csrf=False)
    def website_estimated_delivery_time(self, **kwargs):
        """Returns the estimated delivery time and messages"""
        data = {'product_base_availability': 'False',
                'website_base_availability': 'False',
                'available_message': '', 'unavailable_message': ''}
        days = []
        product_id = request.env['product.template'].browse(
            int(kwargs.get('product_id')))
        message = request.env['website.estimated.delivery.time'].search([])
        if product_id.overwrite_existing_config:
            for rec in product_id.product_estimated_delivery_time_ids:
                if rec.pin == kwargs.get('pin_number'):
                    days.append(rec.days)
                    data['product_base_availability'] = 'True'
                    if days:
                        data['available_message'] = ' '.join(
                            [str(message.available_message), str(days[0]),
                             'Days'])
        else:
            website_wizard = request.env[
                'website.estimated.delivery.time'].search([])
            for rec in website_wizard.estimated_delivery_time_ids:
                if rec.pin == kwargs.get('pin_number'):
                    days.append(rec.days)
                    data['website_base_availability'] = 'True'
            if days:
                if message.display_mode == 'exact':
                    data['available_message'] = ' '.join(
                        [str(message.available_message), str(days[0]), 'Days'])
                else:
                    if message.delivery_day_range == 'days_after':
                        data['available_message'] = ' '.join(
                            [str(message.available_message), str(days[0]), '-',
                             str(days[0] + message.number_of_days), 'Days'])
                    else:
                        if days[0] - message.number_of_days < 0:
                            days_before = 0
                        else:
                            days_before = days[0] - message.number_of_days
                        data['available_message'] = ' '.join(
                            [str(message.available_message),
                             str(days_before), '-',
                             str(days[0]), 'Days'])
        data['unavailable_message'] = message.unavailable_message
        return data
