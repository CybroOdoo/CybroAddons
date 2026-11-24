# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale
import logging

_logger = logging.getLogger(__name__)

def _parse_price_range(price_range_str):
    """
    Parses price range strings into (low, high) float tuples.
    Supports formats: '0-5000', '5000-10000', '50000+', '50000-plus', or URL space-decoded '50000 '.
    """
    if not price_range_str:
        return None, None
    val = str(price_range_str).strip()
    if '-' in val and not val.endswith('-plus'):
        parts = val.split('-')
        try:
            low = float(parts[0])
            high = float(parts[1])
            return low, high
        except (ValueError, IndexError):
            pass
    if '+' in val or val.endswith('plus') or val.endswith(' ') or val.replace('.', '', 1).isdigit():
        clean_val = val.replace('+', '').replace('-plus', '').replace('plus', '').strip()
        try:
            low = float(clean_val)
            return low, None
        except ValueError:
            pass
    return None, None


class CustomWebsiteSale(WebsiteSale):
    """
    Custom controller inheriting from WebsiteSale to manage property listings
    and inject property-specific data into the website rendering context.
    """
    def _get_shop_domain(self, search, category, attribute_value_dict, search_in_description=True):
        """
        Overrides the shop domain to restrict results to properties and apply 
        custom filters (Listing Type, Property Type, Beds, Baths, Price, Amenities).
        """
        domain = super(CustomWebsiteSale, self)._get_shop_domain(search, category, attribute_value_dict, search_in_description)
        
        # Force only properties defined in this theme module
        theme_products = request.env['ir.model.data'].sudo().search([
            ('module', '=', 'theme_livelo'),
            ('model', '=', 'product.template')
        ])
        theme_product_ids = theme_products.mapped('res_id')
        domain = expression.AND([domain, [('id', 'in', theme_product_ids), ('is_property', '=', True)]])
        
        # Get query/post parameters safely
        req_args = request.httprequest.args
        params = request.params
        
        # Filter: Location
        location = params.get('location') or req_args.get('location')
        if location:
            domain = expression.AND([domain, [('location', 'ilike', location)]])
            
        # Filter: Listing Type (rent/sale)
        listing = params.get('listing') or req_args.get('listing')
        if listing in ['rent', 'sale']:
            domain = expression.AND([domain, [('listing_type', '=', listing)]])
            
        # Filter: Property Type (house/villa/etc)
        prop_type = params.get('type') or req_args.get('type')
        if prop_type:
            domain = expression.AND([domain, [('property_type', '=', prop_type)]])
            
        # Filter: Bedrooms
        beds = params.get('beds') or req_args.get('beds')
        if beds:
            try:
                b_val = int(beds)
                if b_val >= 4:
                    domain = expression.AND([domain, [('bed', '>=', 4)]])
                else:
                    domain = expression.AND([domain, [('bed', '=', b_val)]])
            except ValueError:
                pass
                
        # Filter: Bathrooms
        baths = params.get('baths') or req_args.get('baths')
        if baths:
            try:
                bt_val = int(baths)
                if bt_val >= 3:
                    domain = expression.AND([domain, [('bath', '>=', 3)]])
                else:
                    domain = expression.AND([domain, [('bath', '=', bt_val)]])
            except ValueError:
                pass

        # Filter: Price Range
        price_range = params.get('price_range') or req_args.get('price_range')
        low, high = _parse_price_range(price_range)
        if low is not None and high is not None:
            domain = expression.AND([domain, [('list_price', '>=', low), ('list_price', '<=', high)]])
        elif low is not None and high is None:
            domain = expression.AND([domain, [('list_price', '>=', low)]])

        # Filter: Amenities
        selected_amenities = req_args.getlist('amenities')
        if selected_amenities:
            amenity_ids = [int(a) for a in selected_amenities if a.isdigit()]
            if amenity_ids:
                for a_id in amenity_ids:
                    domain = expression.AND([domain, [('amenity_ids', 'in', a_id)]])

        return domain

    def _get_search_order(self, post):
        """
        Handles custom sorting options for properties.
        """
        sort = post.get('sort')
        if sort == 'newest':
            return 'create_date desc, id desc'
        elif sort == 'price_asc':
            return 'list_price asc, id desc'
        elif sort == 'price_desc':
            return 'list_price desc, id desc'
        return super(CustomWebsiteSale, self)._get_search_order(post)

    def _shop_lookup_products(self, options, post, search, website):
        """
        Overrides the Odoo 19 product lookup to strictly filter by our theme properties
        and enforce listing_type, location, property type, beds, baths, price, and amenities filters.
        """
        fuzzy_search_term, product_count, search_result = super(CustomWebsiteSale, self)._shop_lookup_products(options, post, search, website)
        
        # Force only theme properties
        theme_products = request.env['ir.model.data'].sudo().search([
            ('module', '=', 'theme_livelo'),
            ('model', '=', 'product.template')
        ])
        theme_product_ids = theme_products.mapped('res_id')
        
        # Filter search_result to only theme property IDs and properties
        search_result = search_result.filtered(lambda p: p.id in theme_product_ids and p.is_property)

        req_args = request.httprequest.args
        params = request.params

        # Filter: Location
        location = params.get('location') or req_args.get('location') or post.get('location')
        if location:
            search_result = search_result.filtered(lambda p: location.lower() in (p.location or '').lower())

        # Filter: Listing Type (rent/sale)
        listing = params.get('listing') or req_args.get('listing') or post.get('listing')
        if listing in ['rent', 'sale']:
            search_result = search_result.filtered(lambda p: p.listing_type == listing)

        # Filter: Property Type
        prop_type = params.get('type') or req_args.get('type') or post.get('type')
        if prop_type:
            search_result = search_result.filtered(lambda p: p.property_type == prop_type)

        # Filter: Bedrooms
        beds = params.get('beds') or req_args.get('beds') or post.get('beds')
        if beds:
            try:
                b_val = int(beds)
                if b_val >= 4:
                    search_result = search_result.filtered(lambda p: (p.bed or 0) >= 4)
                else:
                    search_result = search_result.filtered(lambda p: (p.bed or 0) == b_val)
            except ValueError:
                pass

        # Filter: Bathrooms
        baths = params.get('baths') or req_args.get('baths') or post.get('baths')
        if baths:
            try:
                bt_val = int(baths)
                if bt_val >= 3:
                    search_result = search_result.filtered(lambda p: (p.bath or 0) >= 3)
                else:
                    search_result = search_result.filtered(lambda p: (p.bath or 0) == bt_val)
            except ValueError:
                pass

        # Filter: Price Range
        price_range = params.get('price_range') or req_args.get('price_range') or post.get('price_range')
        low, high = _parse_price_range(price_range)
        if low is not None and high is not None:
            search_result = search_result.filtered(lambda p: low <= (p.list_price or 0.0) <= high)
        elif low is not None and high is None:
            search_result = search_result.filtered(lambda p: (p.list_price or 0.0) >= low)

        # Filter: Amenities
        selected_amenities = req_args.getlist('amenities')
        if not selected_amenities and post.get('amenities'):
            am_post = post.get('amenities')
            selected_amenities = am_post if isinstance(am_post, list) else [am_post]
        if selected_amenities:
            amenity_ids = [int(a) for a in selected_amenities if str(a).isdigit()]
            for a_id in amenity_ids:
                search_result = search_result.filtered(lambda p: a_id in p.amenity_ids.ids)

        product_count = len(search_result)
        return fuzzy_search_term, product_count, search_result

    @http.route([
        '/shop',
        '/shop/page/<int:page>',
        '/shop/category/<model("product.public.category"):category>',
        '/shop/category/<model("product.public.category"):category>/page/<int:page>',
    ], type='http', auth="public", website=True, sitemap=True)
    def shop(self, page=0, category=None, search='', min_price=0.0, max_price=0.0, ppg=False, **post):
        """
        Overrides the shop route to inject property-specific data.
        """
        response = super(CustomWebsiteSale, self).shop(
            page=page,
            category=category,
            search=search,
            min_price=min_price,
            max_price=max_price,
            ppg=ppg,
            **post
        )

        if not hasattr(response, 'qcontext'):
            return response

        values = response.qcontext
        
        # Fetch dynamic filter data
        all_amenities = request.env['property.amenity'].sudo().search([])
        selected_amenities = [int(a) for a in request.httprequest.args.getlist('amenities') if a.isdigit()]
        
        # Get theme product IDs for the sidebar filter
        theme_products = request.env['ir.model.data'].sudo().search([
            ('module', '=', 'theme_livelo'),
            ('model', '=', 'product.template')
        ])
        theme_product_ids = theme_products.mapped('res_id')

        # Latest properties for sidebar (strictly theme properties only)
        latest_properties = request.env['product.template'].sudo().search([
            ('id', 'in', theme_product_ids),
            ('website_published', '=', True)
        ], order='create_date desc', limit=6)

        req_args = request.httprequest.args
        listing_val = request.params.get('listing') or req_args.get('listing') or ''

        # Add property-specific data to values
        values.update({
            'total_count': values.get('search_count', 0),
            'properties': values.get('products', []),
            'search': search,
            'location': request.params.get('location') or req_args.get('location') or '',
            'filter_type': request.params.get('type') or req_args.get('type') or '',
            'listing_type': listing_val, 
            'filter_beds': request.params.get('beds') or req_args.get('beds') or '',
            'filter_baths': request.params.get('baths') or req_args.get('baths') or '',
            'price_range': request.params.get('price_range') or req_args.get('price_range') or '',
            'per_page': request.params.get('per_page') or req_args.get('per_page') or '12',
            'sort': request.params.get('sort') or req_args.get('sort') or 'newest',
            'all_amenities': all_amenities,
            'selected_amenities': selected_amenities,
            'latest_properties': latest_properties,
        })

        # Force our custom property listing template
        response.template = 'theme_livelo.property_listing_page'
        return response

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        """
        Overrides the product details route to use a custom property detail page template.
        """
        response = super(CustomWebsiteSale, self).product(product=product, category=category, search=search, **kwargs)
        if hasattr(response, 'qcontext'):
            response.template = 'theme_livelo.property_detail_page'
            # Fetch all internal users to list as potential salespersons
            salespersons = request.env['res.users'].sudo().search([('share', '=', False)])
            response.qcontext['salespersons'] = salespersons
        return response

    @http.route('/property/contact', type='http', auth="public", methods=['POST'], website=True, csrf=True)
    def property_contact(self, **post):
        product_id = post.get('product_id')
        product = request.env['product.template'].sudo().browse(int(product_id)) if product_id else None
        
        lead_vals = {
            'name': f"Interest in {product.name}" if product else "Property Lead",
            'contact_name': post.get('contact_name'),
            'phone': post.get('mobile'),
            'email_from': post.get('email'),
            'description': post.get('message'),
            'user_id': product.salesperson_id.id if (product and product.salesperson_id) else False,
        }
        
        # Create Lead in CRM
        request.env['crm.lead'].sudo().create(lead_vals)
        
        return request.render('theme_livelo.property_contact_thanks', {})

    @http.route(['/service', '/location'], type='http', auth="public", website=True, sitemap=True)
    def location_service_page(self, **kwargs):
        """
        Serves the Location/Service page directly to public users without relying on stale database website.page records.
        """
        return request.render('theme_livelo.service_page', {})

    @http.route('/pricing', type='http', auth="public", website=True, sitemap=True)
    def pricing_page(self, **kwargs):
        """
        Serves the Pricing page directly.
        """
        return request.render('theme_livelo.pricing_page', {})

    @http.route('/aboutus', type='http', auth="public", website=True, sitemap=True)
    def about_us_page(self, **kwargs):
        """
        Serves the About Us page directly.
        """
        return request.render('theme_livelo.about_us_page', {})

