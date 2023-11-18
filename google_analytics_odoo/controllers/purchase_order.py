# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gokul PI (<https://www.cybrosys.com>)
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


class PurchaseDetails(http.Controller):
    @http.route('/purchase_analytics', type="json", auth="public")
    def purchase_details(self, **kw):
        """Returns the purchase order details"""
        order = request.env['purchase.order'].browse(
            int(kw.get('order_id'))).read()
        return {
            'purchase_data': {'name': order[0].get('name'),
                              'amount': order[0].get('amount_total'),
                              'customer': order[0].get('partner_id')[1]}
        }
