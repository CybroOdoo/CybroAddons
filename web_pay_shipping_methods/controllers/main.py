# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<http://www.cybrosys.com>).
#    Author: Mruthul Raj(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU AFFERO GENERAL
#    PUBLIC LICENSE (AGPL v3), Version 3.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import http
from odoo.http import request


class WebPayShippingMethods(http.Controller):

    @http.route('/web/deliver/carrier', type='json', auth='public', website=True)
    def get_delivery_carriers(self, **kwargs):
        provider_id = kwargs.get('provider_id')
        payment_provider = request.env['payment.provider'].sudo().browse(provider_id)
        return payment_provider.delivery_carrier_ids.ids
