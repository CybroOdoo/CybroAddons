# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Vishnu KP(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, http, _
from odoo.http import request


class CustomerPortal(http.Controller):
    """Used to manage a customer portal"""

    @http.route(['/my/prebook_request/<model("product.template"):product>'],
                type='http', auth="public", website=True)
    def portal_my_employee_request(self, product, **kwargs):
        """Pre-book button to pre-book the product"""
        vals = {
            'product': product.id,
        }
        current_user = request.env['res.users'].sudo().browse(
            request.session.uid)
        partner = current_user.partner_id
        product_qty = int(kwargs.get('prod_qty'))
        if request.session.uid:

            pre_booking = request.env['website.prebook'].sudo().create({
                'partner_id': partner.id,
                'booking_date': fields.datetime.today(),
                'product_id': product.id,
                'quantity': product_qty,
                'website_id': request.website.id,
            })
            if pre_booking:
                max_quantity = product.pre_max_quantity
                product.sudo().write({'pre_max_quantity': int(max_quantity - product_qty)})

            return request.render("website_pre_booking.pre_booking_done",
                                  {'ref': pre_booking.reference})
        else:
            return request.render("website_pre_booking.prebook_address", vals)

    @http.route(['/prebook/address'], type='http', methods=['GET', 'POST'],
                auth="public", website=True, sitemap=False)
    def pre_address(self, **kw):
        print('If not login create a new user', **kw)
        """If not login, create a new user"""
        product = request.env['product.template'].sudo().browse(
            int(kw.get('product')))
        partner = request.env['res.partner'].sudo().create({
            'name': kw.get('name'),
            'email': kw.get('email'),
            'phone': kw.get('phone'),
        })
        pre_booking = request.env['website.prebook'].sudo().create({
            'partner_id': partner.id,
            'booking_date': fields.datetime.today(),
            'product_id': product.id})
        if pre_booking:
            max_quantity = product.pre_max_quantity
            product.pre_max_quantity = max_quantity - 1
        return request.render("website_pre_booking.pre_booking_done",
                              {'ref': pre_booking.reference})

    @http.route('/track/prebooking', website=True, auth='user', csrf=False)
    def submit_booking(self, **kwargs):
        """For tracking the specific pre-orders using refernce code"""
        bookings = request.env['website.prebook'].sudo().search(
            [('reference', '=', kwargs.get('reference'))])
        if bookings and bookings.sale_id:
            if bookings.sale_id.state == 'draft':
                state = 'Quotation'
            elif bookings.sale_id.state == 'sent':
                state = 'Quotation Sent'
            elif bookings.sale_id.state == 'sale':
                state = 'Sales Order'
            elif bookings.sale_id.state == 'done':
                state = 'Locked'
            elif bookings.sale_id.state == 'cancel':
                state = 'Cancelled'
            vals = {
                'reference': bookings.reference,
                'product': bookings.product_id.name,
                'status': state if bookings.sale_id else bookings.state,
                'date': bookings.booking_date,
            }
            return request.render("website_pre_booking.my_booking_template",
                                  vals)
        else:
            return request.render("website_pre_booking.my_booking_template",
                                  {'vals': True})

    @http.route(['/my/prebookings', '/my/prebookings/page/<int:page>'],
                type='http', auth="user", website=True)
    def my_prebookings(self):
        """Can track the pre bookings from the website"""
        value = []
        values = {'value': value}
        return request.render("website_pre_booking.my_booking_template", values)

    @http.route(['/sale/fail'], type='http', auth="user", website=True)
    def my_prebookings_fail(self):
        """Can track the pre bookings from the website"""
        return request.render("website_pre_booking.pre_booking_failed")
