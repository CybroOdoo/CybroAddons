# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

from odoo import http
from odoo.http import request, route


class TextileManagement(http.Controller):
    """For textile management"""

    @http.route(['/textile/inquiry/form'], type='http', auth='public',
                website=True)
    def textile_inquiry_form(self):
        """For textile inquiry form"""
        return request.render(
            "textile_management.textile_inquiry_form", {})

    @route('/textile/inquiry/form/submit', type='http', auth='public',
           methods=['POST'], csrf=False, website=True)
    def textile_inquiry_form_submit(self, **kwargs):
        """For saving data to backend from website form"""
        request.env['website.inquiry'].sudo().create({
            'inquirer': kwargs.get('name'),
            'email': kwargs.get('email'),
            'phone_number': kwargs.get('number'),
            'description': kwargs.get('description'),
        })
        return request.redirect('/textile/inquiry/form?submitted=1')

    @http.route('/customer/review/session', type='json', auth='public',
                website=True, csrf=False)
    def save_review(self, rating=None, comment=None, **kwargs):
        """Write customer rating/comment directly onto the active sale order.

        sale_get_order() was removed in Odoo 19. The order ID is already in
        the session as 'sale_order_id', so we browse it directly instead.
        """
        if not rating:
            return False

        order_id = request.session.get('sale_order_id')
        if not order_id:
            return False

        order = request.env['sale.order'].sudo().browse(order_id)
        if not order.exists():
            return False

        vals = {'rating': str(rating)}
        if comment is not None:
            vals['comment'] = comment

        order.write(vals)
        return True