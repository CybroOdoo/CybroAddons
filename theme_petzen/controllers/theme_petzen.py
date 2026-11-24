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
# Odoo 17 has no `env._`; `odoo._` is the supported translation helper.
# pylint: disable=prefer-env-translation
import logging

from odoo import http, _
from odoo.http import request
from odoo.tools import email_normalize, html2plaintext

_logger = logging.getLogger(__name__)


class PetzenServices(http.Controller):
    """Website pages, forms and JSON endpoints of the Petzen theme."""

    @http.route(['/services'], type='http', auth="public", website=True, sitemap=True)
    def services(self, **kw):
        """Render the services page."""
        return request.render("theme_petzen.services_page_template", {})

    @http.route(['/about'], type='http', auth="public", website=True, sitemap=True)
    def about(self, **kw):
        """Render the about page."""
        return request.render("theme_petzen.about_page_template", {})

    @http.route(['/reviews'], type='http', auth="public", website=True, sitemap=True)
    def reviews(self, **kw):
        """Render the customer reviews page."""
        return request.render("theme_petzen.reviews_page_template", {})

    @http.route(['/theme_petzen/get_reviews_data'], type='json', auth="public", website=True)
    def get_reviews_data(self, limit=12, **kw):
        """Return approved customer reviews for the dynamic reviews widget."""
        reviews = request.env['petzen.review'].sudo().search(
            [('state', '=', 'approved')],
            limit=min(int(limit or 12), 50),
            order='create_date desc'
        )
        review_list = []
        for r in reviews:
            initials = ''.join(p[0] for p in (r.name or '?').split()[:2]).upper()
            review_list.append({
                'id': r.id,
                'name': r.name,
                'rating': r.rating,
                'review': r.review,
                'initials': initials,
                'stars': '★' * r.rating,
                'empty_stars': '★' * (5 - r.rating) if r.rating < 5 else '',
            })
        return {
            'reviews': review_list,
        }

    @http.route(['/contact'], type='http', auth="public", website=True, sitemap=True)
    def contact(self, **kw):
        """Render the contact page."""
        return request.render("website.contactus", {})

    # ── Forms ────────────────────────────────────────────────────────────────

    @http.route(['/reviews/submit'], type='json', auth="public", website=True)
    def submit_review(self, **kw):
        """Save a petzen.review; it is shown on /reviews once approved."""
        name = (kw.get('name') or '').strip()
        email = (kw.get('email') or '').strip()
        review = (kw.get('review') or '').strip()
        if not name or not email or not review:
            return {'success': False, 'error': _('Please fill in all required fields.')}
        if not email_normalize(email):
            return {'success': False, 'error': _('Please enter a valid email address.')}
        try:
            rating = min(max(int(kw.get('rating') or 5), 1), 5)
        except (TypeError, ValueError):
            rating = 5
        try:
            request.env['petzen.review'].sudo().create({
                'name': name,
                'email': email,
                'rating': rating,
                'review': review,
            })
        except Exception:
            _logger.exception("Petzen: could not save review")
            return {'success': False, 'error': _('Something went wrong. Please try again.')}
        return {'success': True}

    @http.route(['/contact/submit'], type='json', auth="public", website=True)
    def submit_contact(self, **kw):
        """Create a CRM lead from the contact form submission."""
        first_name = (kw.get('first_name') or '').strip()
        last_name = (kw.get('last_name') or '').strip()
        email = (kw.get('email') or '').strip()
        phone = (kw.get('phone') or '').strip()
        department = (kw.get('department') or '').strip()
        message = (kw.get('message') or '').strip()

        if not first_name or not email or not message:
            return {'success': False, 'error': _('Please fill in all required fields.')}
        if not email_normalize(email):
            return {'success': False, 'error': _('Please enter a valid email address.')}

        description = ''
        if department:
            description += 'Topic: %s\n\n' % department
        description += message
        return self._create_lead({
            'name': '[Petzen] %s' % (department or 'General Inquiry'),
            'contact_name': ('%s %s' % (first_name, last_name)).strip(),
            'email_from': email,
            'phone': phone or False,
            'description': description,
        })

    @http.route(['/services/book'], type='json', auth="public", website=True)
    def book_service(self, **kw):
        """Create a CRM lead from the service booking form."""
        values = {key: (kw.get(key) or '').strip() for key in (
            'pet_name', 'pet_type', 'service', 'owner_name', 'email', 'phone', 'date', 'notes')}
        if not all(values[key] for key in ('pet_name', 'pet_type', 'service', 'owner_name', 'email', 'date')):
            return {'success': False, 'error': _('Please fill in all required fields.')}
        if not email_normalize(values['email']):
            return {'success': False, 'error': _('Please enter a valid email address.')}

        description = '\n'.join([
            'Service: %s' % values['service'],
            'Pet: %s (%s)' % (values['pet_name'], values['pet_type']),
            'Preferred date: %s' % values['date'],
        ])
        if values['notes']:
            description += '\n\nNotes:\n%s' % values['notes']
        return self._create_lead({
            'name': '[Petzen Booking] %s for %s' % (values['service'], values['pet_name']),
            'contact_name': values['owner_name'],
            'email_from': values['email'],
            'phone': values['phone'] or False,
            'description': description,
        })

    @http.route(['/petzen/newsletter'], type='json', auth="public", website=True)
    def newsletter(self, email=None, **kw):
        """Create a CRM lead from the newsletter subscription form."""
        email = (email or '').strip()
        if not email_normalize(email):
            return {'success': False, 'error': _('Please enter a valid email address.')}
        return self._create_lead({
            'name': '[Petzen] Newsletter subscription',
            'email_from': email,
            'description': 'Subscribed from the website footer.',
        })

    def _create_lead(self, values):
        """Create a CRM lead from the given values and return the result for the JS caller."""
        try:
            request.env['crm.lead'].sudo().create(dict(values, type='lead'))
        except Exception:
            _logger.exception("Petzen: could not create lead")
            return {'success': False, 'error': _('Something went wrong. Please try again.')}
        return {'success': True}

    # ── Live blocks of the home page snippets ────────────────────────────────

    @http.route(['/petzen/home/categories'], type='json', auth="public", website=True)
    def home_categories(self, **kw):
        """Return the rendered category tiles for the categories snippet."""
        html = request.env['ir.ui.view']._render_template(
            'theme_petzen.pz_category_bento', {'website': request.website})
        return {'html': html}

    @http.route(['/petzen/home/products'], type='json', auth="public", website=True)
    def home_products(self, limit=12, **kw):
        """Return the rendered product tabs and carousel for the products snippet."""
        try:
            limit = min(max(int(limit or 12), 1), 24)
        except (TypeError, ValueError):
            limit = 12
        website = request.website
        html = request.env['ir.ui.view']._render_template('theme_petzen.pz_products_dynamic', {
            'website': website,
            'pz_products': website._petzen_products(limit=limit),
        })
        return {'html': html}

    # ── Wishlist (heart of the product cards) ────────────────────────────────

    @http.route(['/petzen/wishlist/toggle'], type='json', auth="public", website=True)
    def wishlist_toggle(self, product_id, **kw):
        """Add / remove a product variant to the website_sale_wishlist wishlist.
        Returns the new state and the wishlist product ids (same format as
        /shop/wishlist?count=1, kept in sessionStorage by the wishlist JS)."""
        if 'product.wishlist' not in request.env:
            return {'available': False}
        Wishlist = request.env['product.wishlist']
        product = request.env['product.product'].browse(int(product_id)).exists()
        if not product or not product.sudo().product_tmpl_id.website_published:
            return {'available': True, 'in_wishlist': False, 'error': _('This product is not available.')}

        wishes = Wishlist.current()
        existing = wishes.filtered(lambda w: w.product_id == product)
        if existing:
            if request.website.is_public_user():
                session_ids = request.session.get('wishlist_ids') or []
                request.session['wishlist_ids'] = [wid for wid in session_ids if wid not in existing.ids]
                existing.sudo().unlink()
            else:
                existing.unlink()
            in_wishlist = False
        else:
            partner_id = False if request.website.is_public_user() else request.env.user.partner_id.id
            pricelist = request.website.pricelist_id
            wish = (Wishlist.sudo() if not partner_id else Wishlist)._add_to_wishlist(
                pricelist.id,
                pricelist.currency_id.id,
                request.website.id,
                product._get_combination_info_variant()['price'],
                product.id,
                partner_id,
            )
            if not partner_id:
                request.session['wishlist_ids'] = (request.session.get('wishlist_ids') or []) + [wish.id]
            in_wishlist = True

        product_ids = Wishlist.current().product_id.ids
        return {
            'available': True,
            'in_wishlist': in_wishlist,
            'count': len(product_ids),
            'product_ids': product_ids,
        }

    # ── Search overlay ───────────────────────────────────────────────────────

    @http.route(['/petzen/search'], type='json', auth="public", website=True)
    def search_products(self, term='', limit=8, **kw):
        """Return the products matching the search term for the search overlay."""
        website = request.website
        domain = website._petzen_product_domain()
        term = (term or '').strip()
        if term:
            domain += ['|', '|', ('name', 'ilike', term),
                       ('public_categ_ids.name', 'ilike', term), ('categ_id.name', 'ilike', term)]
        products = request.env['product.template'].search(domain, limit=min(int(limit or 8), 24))
        fiscal_position = request.env['account.fiscal.position'].sudo()._get_fiscal_position(
            request.env.user.partner_id)
        prices = products._get_sales_prices(website.pricelist_id, fiscal_position)
        currency = website.currency_id
        Monetary = request.env['ir.qweb.field.monetary']
        results = []
        for product in products:
            price = prices.get(product.id, {})
            price_reduce = price.get('price_reduce', product.list_price)
            base_price = price.get('base_price')
            direct_add = product.product_variant_count == 1 and product._is_add_to_cart_possible()
            ribbon = product.sudo().website_ribbon_id
            results.append({
                'name': product.name,
                'url': product.website_url,
                'image': '/web/image/product.template/%s/image_256' % product.id,
                'tag': product.public_categ_ids[:1].name or product.categ_id.name or '',
                'price': Monetary.value_to_html(price_reduce, {'display_currency': currency}),
                'price_old': base_price and Monetary.value_to_html(base_price, {'display_currency': currency}) or '',
                'badge': ('−%d%%' % round(100 - price_reduce * 100 / base_price)) if base_price
                else html2plaintext(ribbon.html or ''),
                'is_new': not base_price and bool(ribbon),
                'product_id': product.product_variant_id.id if direct_add else False,
            })
        return {'results': results}
