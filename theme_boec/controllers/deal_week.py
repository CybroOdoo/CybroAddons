# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class DealWeek(http.Controller):

    @http.route('/get_product', auth='public', type='json', website=True)
    def get_products(self, **kwargs):
        boec_configuration = request.env.ref('theme_boec.boec_config_data')
        product_id = boec_configuration.deal_week_product_id
        values = {'product_id': product_id}
        response = http.Response(template='theme_boec.deal_week', qcontext=values)
        return response.render()

    @http.route('/get_countdown', auth='public', type='json', website=True)
    def get_countdown(self, **kwargs):
        boec_configuration = request.env.ref('theme_boec.boec_config_data')
        end_date = boec_configuration.date_end
        return end_date
