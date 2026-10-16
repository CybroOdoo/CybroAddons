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
"""
This module defines the theme_cordage components for theme_cordage.
"""
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website

class CordageWebsite(Website):
    """Controller to override the default website homepage behavior."""
    @http.route('/', type='http', auth="public", website=True, sitemap=True)
    def index(self, **kw):
        """Render homepage — let website.homepage render (theme extension applied
        automatically by Odoo's view inheritance). Inject Cordage products into
        the template context so s_featured_products can access them."""
        if request.website.theme_id and 'cordage' in (request.website.theme_id.name or '').lower():
            Product = request.env['product.template'].sudo()
            cordage_products = Product.search([
                ('website_published', '=', True),
                ('sale_ok', '=', True),
            ], limit=8, order='website_sequence asc, id asc')
            cordage_categories = cordage_products.mapped('public_categ_ids')
            # Limit to top 4 categories to keep tabs short
            cordage_categories = cordage_categories.filtered(lambda c: not c.parent_id) or cordage_categories
            cordage_categories = cordage_categories[:4]
            # Store in request context so t-call'd snippets can read them
            request.env.context = dict(request.env.context, cordage_products=cordage_products, cordage_categories=cordage_categories)
        return super().index(**kw)

class CordageController(http.Controller):
    """Controller for managing custom pages in the Cordage theme."""

    @http.route('/industries', type='http', auth='public', website=True,
                sitemap=True)
    def cordage_industries(self, **kw):
        """Render the Industries page."""
        return request.render('theme_cordage.industries_page', {})

    @http.route('/about', type='http', auth='public', website=True,
                sitemap=True)
    def cordage_about(self, **kw):
        """Render the About page."""
        return request.render('theme_cordage.about_page', {})

    @http.route('/cordage-contact', type='http', auth='public', website=True,
                sitemap=True)
    def cordage_contact(self, **kw):
        """Render the Contact page."""
        return request.render('theme_cordage.contact_page', {})

    @http.route('/cordage-contact/submit', type='http', auth='public',
                website=True, methods=['POST'], csrf=True)
    def cordage_contact_submit(self, **post):
        """Handle contact form submissions — sends email to admin."""
        firstname = post.get('firstname', '').strip()
        lastname = post.get('lastname', '').strip()
        name = f"{firstname} {lastname}".strip() or 'Anonymous'
        email = post.get('email', '').strip()
        company = post.get('company', '').strip()
        subject = post.get('subject', 'Cordage Website Enquiry')
        message_body = post.get('message', '').strip()
        admin_email = request.env['ir.config_parameter'].sudo().get_param(
            'web.base.url', 'admin@example.com')
        recipient = request.env.user.email or 'admin@example.com'
        company_line = (f'<p><b>Company:</b> {company}</p>'
                        if company else '')
        request.env['mail.mail'].sudo().create({
            'subject': f'[Cordage] {subject}',
            'body_html': (
                f'<p><b>Name:</b> {name}</p>'
                f'<p><b>Email:</b> {email}</p>'
                f'{company_line}'
                f'<p><b>Subject:</b> {subject}</p>'
                f'<p><b>Message:</b><br/>{message_body}</p>'
            ),
            'email_to': recipient,
            'email_from': email or 'noreply@cordage.com',
        }).send()
        return request.render('theme_cordage.contact_page', {
            'contact_success': True,
        })

    @http.route('/cordage-shop', type='http', auth='public', website=True, sitemap=True)
    def cordage_shop(self, category=None, search='', min_price=0, max_price=0, sort='featured', **post):
        """Render the custom Shop page with dynamic backend filtering."""
        Product = request.env['product.template'].sudo()
        Category = request.env['product.public.category'].sudo()
        Attribute = request.env['product.attribute'].sudo()
        domain = [('sale_ok', '=', True), ('website_published', '=', True)]
        # Search filter
        if search:
            domain += [('name', 'ilike', search)]
        # Category filter
        if category and category != 'all':
            try:
                cat_id = int(category)
                domain += [('public_categ_ids', 'child_of', cat_id)]
            except ValueError:
                pass
        # Price filter
        if min_price:
            domain += [('list_price', '>=', float(min_price))]
        if max_price:
            domain += [('list_price', '<=', float(max_price))]
        # Attribute filters (material, diameter)
        # Assuming URL params like ?attr_1=2&attr_3=4
        active_attrs = []
        for key in request.httprequest.args:
            if key.startswith('attr_'):
                vals = []
                for value in request.httprequest.args.getlist(key):
                    try:
                        val_id = int(value)
                        vals.append(val_id)
                        active_attrs.append(val_id)
                    except ValueError:
                        pass
                if vals:
                    domain += [('attribute_line_ids.value_ids', 'in', vals)]
        # Sorting
        order_mapping = {
            'featured': 'website_sequence asc, id desc',
            'price-asc': 'list_price asc, id desc',
            'price-desc': 'list_price desc, id desc',
            'name': 'name asc, id desc',
        }
        order = order_mapping.get(sort, 'website_sequence asc, id desc')
        # Fetch products
        products = Product.search(domain, order=order)
        # Fetch parent categories for the chips
        parent_categories = Category.search([('parent_id', '=', False)])
        # Fetch all categories for the sidebar
        all_categories = Category.search([])
        # We fetch all attributes to build the filters
        attributes = Attribute.search([])
        # Determine if we are in demo mode (no published products in the DB)
        demo_mode = Product.search_count([('sale_ok', '=', True), ('website_published', '=', True)]) == 0

        return request.render('theme_cordage.shop_page', {
            'products': products,
            'categories': all_categories,
            'parent_categories': parent_categories,
            'attributes': attributes,
            'active_category': int(category) if category and category != 'all' else 'all',
            'search': search,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort,
            'active_attrs': active_attrs,
            'demo_mode': demo_mode,
        })

    @http.route('/cordage-product', type='http', auth='public', website=True, sitemap=True)
    def cordage_product(self, id=None, **kw):
        """Render the custom Product page."""
        Product = request.env['product.template'].sudo()
        product = Product.browse(int(id)) if id else None
        # If no product_id was provided, or it's not published, return 404
        if not product or not product.website_published:
            raise request.not_found()
        return request.render('theme_cordage.product_page_page', {
            'product': product
        })

    @http.route('/cordage/cart/data', type='json', auth='public', website=True)
    def cordage_cart_data(self, **kw):
        """Get cart data."""
        order = request.website.sale_get_order()
        if not order:
            return {'cart': [], 'subtotal': 0, 'shipping': 0, 'total': 0}
        cart = []
        for line in order.website_order_line:
            if not line.product_id:
                continue
            cart.append({
                'id': line.product_id.id,
                'line_id': line.id,
                'name': line.product_id.name,
                'price': line.price_unit,
                'qty': int(line.product_uom_qty),
                'imgUrl': '/web/image/product.template/%d/image_128' % line.product_id.product_tmpl_id.id,
                'unit': line.product_uom.name if line.product_uom else ''
            })
        return {
            'cart': cart,
            'subtotal': order.amount_untaxed,
            'shipping': order.amount_delivery if hasattr(order, 'amount_delivery') else 0,
            'total': order.amount_total
        }