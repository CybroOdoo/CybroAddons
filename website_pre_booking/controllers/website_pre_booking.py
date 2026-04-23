# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anupriya Ashok(<https://www.cybrosys.com>)
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
from odoo import fields, http
from odoo.http import request


class CustomerPortal(http.Controller):
    """Used to manage a customer portal"""

    @http.route(['/my/prebook_request/<model("product.template"):product>','/my/prebook_request/<int:product_id>'],
                type='http', auth="public", website=True)
    def portal_my_employee_request(self, product=None, product_id=None, **kwargs):
        """Pre-book button to pre-book the product"""
        if not product and product_id:
            product = request.env['product.template'].sudo().browse(product_id)
        elif not product:
            return request.redirect('/shop')
        if not product.exists() or not product.pre_book:
            return request.redirect('/shop')
        current_user = request.env['res.users'].sudo().browse(request.session.uid)
        partner = current_user.partner_id
        product_qty = int(kwargs.get('prod_qty', 0))
        if request.session.uid:
            existing_booking = request.env['website.prebook'].sudo().search([
                ('partner_id', '=', partner.id),
                ('product_id', '=', product.id),
                ('state', '!=', 'cancel')
            ], limit=1)
            if existing_booking:
                return request.render("website_pre_booking.pre_booking_done",
                                      {'ref': existing_booking.reference,
                                       'mainObject': existing_booking
                                       })
            if product_qty <= 0:
                vals = {'product': product.id, 'quantity': product_qty}
                return request.render("website_pre_booking.prebook_address", vals)
            if product_qty > product.pre_max_quantity:
                return request.redirect('/sale/fail')
            pre_booking = request.env['website.prebook'].sudo().create({
                'partner_id': partner.id,
                'booking_date': fields.Datetime.now(),
                'product_id': product.id,
                'quantity': product_qty,
                'website_id': request.website.id,
            })
            if pre_booking:
                product.sudo().write({
                    'pre_max_quantity': int(product.pre_max_quantity - product_qty)
                })
                return request.render("website_pre_booking.pre_booking_done",
                                      {'ref': pre_booking.reference,
                                       'mainObject': pre_booking
                                       })
        else:
            vals = {'product': product.id, 'quantity': product_qty}
            return request.render("website_pre_booking.prebook_address", vals)


    @http.route(['/prebook/address'], type='http', methods=['GET', 'POST'],
                auth="public", website=True, sitemap=False)
    def pre_address(self, **kw):
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
            'booking_date': fields.Datetime.now(),
            'product_id': product.id,
            'quantity': int(kw.get('quantity')),
            'website_id': request.website.id,
        })
        if pre_booking:
            max_quantity = product.pre_max_quantity
            product.pre_max_quantity = max_quantity - 1
        return request.render("website_pre_booking.pre_booking_done",
                              {'ref': pre_booking.reference,
                               })

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
            else:
                state = 'Draft'
        vals = {
            'reference': bookings.reference,
            'product': bookings.product_id.name,
            'status': state if bookings.sale_id else bookings.state,
            'date': bookings.booking_date,
        }
        return request.render("website_pre_booking.my_booking_template",
                              vals)

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
