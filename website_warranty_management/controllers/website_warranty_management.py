# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import http,fields
from odoo.http import request


class WarrantyClaimController(http.Controller):
    """ Class for Warranty claim controller"""

    @http.route('/warranty', type='http', auth="user", website=True)
    def warranty_claim(self):
        """ Function to pass the warranty claim details to the warranty
        claim page"""
        partner = request.env.user.partner_id
        sale_orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('is_warranty_check', '=', True)
        ])
        # Get products from these sale orders that have warranty
        products = sale_orders.mapped('order_line.product_id').filtered(lambda p: p.is_warranty_available)
        
        return request.render('website_warranty_management.warranty_claim_page',
                              {'sale_orders': sale_orders,
                               'customers': partner,
                               'products': products})

    @http.route('/warranty/claim/submit', type='http', auth="user", website=True, csrf=True)
    def warranty_claim_submit(self, **post):
        """ Create a warranty claim record from website submission"""
        if post:
            customer_id = int(post.get('customer_id')) if post.get('customer_id') else False
            sale_order_id = int(post.get('sale_order_id')) if post.get('sale_order_id') else False
            product_id = int(post.get('products_id')) if post.get('products_id') else False
            description = post.get('additional_field')

            # Find matching registration if any
            registration = request.env['warranty.registration'].sudo().search([
                ('sale_order_id', '=', sale_order_id),
                ('product_id', '=', product_id)
            ], limit=1)

            if registration and registration.state == 'expired':
                return request.render('website_warranty_management.warranty_expired_view', {
                    'expiry_date': registration.expiry_date,
                    'product_name': registration.product_id.name
                })

            vals = {
                'customer_id': customer_id,
                'sale_order_id': sale_order_id,
                'product_id': product_id,
                'warranty_registration_id': registration.id if registration else False,
                'state': 'draft',
            }
            # We could add description to a new field in warranty.claim if needed
            request.env['warranty.claim'].sudo().create(vals)
            
        return request.render('website_warranty_management.claim_thanks_view')

    @http.route('/warranty/register', type='http', auth="user", website=True)
    def warranty_register(self):
        """ Render the warranty registration page"""
        partner = request.env.user.partner_id
        # Get orders that don't have all products registered yet (optional logic)
        sale_orders = request.env['sale.order'].sudo().search([
            ('partner_id', '=', partner.id),
            ('is_warranty_check', '=', True)
        ])
        products = sale_orders.mapped('order_line.product_id').filtered(lambda p: p.is_warranty_available)
        
        return request.render('website_warranty_management.warranty_registration_page', {
            'sale_orders': sale_orders,
            'products': products,
            'customer': partner,
        })

    @http.route('/warranty/register/submit', type='http', auth="user", website=True, csrf=True)
    def warranty_register_submit(self, **post):
        """ Submit warranty registration from website"""
        if post:
            customer_id = int(post.get('customer_id'))
            sale_order_id = int(post.get('sale_order_id'))
            product_id = int(post.get('products_id'))
            serial_no = post.get('serial_no')

            # Create or update registration
            existing = request.env['warranty.registration'].sudo().search([
                ('sale_order_id', '=', sale_order_id),
                ('product_id', '=', product_id)
            ], limit=1)

            if not existing:
                product = request.env['product.product'].sudo().browse(product_id)
                start_date = fields.Date.context_today(request.env.user)
                duration = product.warranty_duration
                period_type = product.warranty_period_type
                
                from dateutil.relativedelta import relativedelta
                if period_type == 'days':
                    expiry_date = start_date + relativedelta(days=duration)
                elif period_type == 'years':
                    expiry_date = start_date + relativedelta(years=duration)
                else: 
                    expiry_date = start_date + relativedelta(months=duration)

                reg = request.env['warranty.registration'].sudo().create({
                    'customer_id': customer_id,
                    'sale_order_id': sale_order_id,
                    'product_id': product_id,
                    'serial_no': serial_no,
                    'start_date': start_date,
                    'expiry_date': expiry_date,
                    'warranty_type': product.warranty_type,
                    'state': 'active'
                })
                reg.action_send_confirmation_email()
            else:
                existing.write({'serial_no': serial_no})
            
            return request.render('website_warranty_management.registration_thanks_view')
        
        return request.redirect('/warranty/register')
                
    @http.route('/warranty/renewal/<model("warranty.registration"):registration>', type='http', auth="user", website=True)
    def warranty_renewal(self, registration):
        """ Create a renewal request from portal"""
        if registration and registration.customer_id.id == request.env.user.partner_id.id:
            request.env['warranty.claim'].sudo().create({
                'customer_id': registration.customer_id.id,
                'sale_order_id': registration.sale_order_id.id,
                'product_id': registration.product_id.id,
                'warranty_registration_id': registration.id,
                'claim_type': 'renewal',
                'state': 'draft',
            })
            return request.render('website_warranty_management.renewal_thanks_view')
        return request.redirect('/my/claims')
