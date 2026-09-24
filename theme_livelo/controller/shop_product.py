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

class CustomWebsiteSale(WebsiteSale):
    """
    Custom controller inheriting from WebsiteSale to manage property listings
    and inject property-specific data into the website rendering context.
    """
    def _get_shop_domain(self, search, category, attrib_values, search_in_description=True):
        """
        Overrides the shop domain to restrict results to properties and apply 
        custom filters (Listing Type, Property Type, Beds, Baths, Price, Amenities, Location).
        """
        domain = super(CustomWebsiteSale, self)._get_shop_domain(search, category, attrib_values, search_in_description)
        # Enforce properties filter
        domain = expression.AND([domain, [('is_property', '=', True)]])
        args = request.httprequest.args
        params = request.params
        # Filter: Location
        location = args.get('location') or params.get('location')
        if location:
            domain = expression.AND([domain, [('location', 'ilike', location.strip())]])
        # Filter: Listing Type (rent/sale)
        listing = args.get('listing') or params.get('listing')
        if listing:
            domain = expression.AND([domain, [('listing_type', '=', listing.strip())]])
        # Filter: Property Type (house/villa/etc)
        prop_type = args.get('type') or params.get('type')
        if prop_type:
            domain = expression.AND([domain, [('property_type', '=', prop_type.strip())]])
        # Filter: Bedrooms
        beds_val = args.get('beds') or params.get('beds')
        if beds_val and str(beds_val).isdigit():
            beds = int(beds_val)
            if beds >= 4:
                domain = expression.AND([domain, [('bed', '>=', 4)]])
            else:
                domain = expression.AND([domain, [('bed', '=', beds)]])
        # Filter: Bathrooms
        baths_val = args.get('baths') or params.get('baths')
        if baths_val and str(baths_val).isdigit():
            baths = int(baths_val)
            if baths >= 3:
                domain = expression.AND([domain, [('bath', '>=', 3)]])
            else:
                domain = expression.AND([domain, [('bath', '=', baths)]])
        # Filter: Price Range
        price_range = args.get('price_range') or params.get('price_range')
        if price_range:
            if '-' in price_range:
                parts = price_range.split('-')
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    low, high = float(parts[0]), float(parts[1])
                    domain = expression.AND([domain, [('list_price', '>=', low), ('list_price', '<=', high)]])
            elif '+' in price_range:
                val = price_range.replace('+', '').strip()
                if val.isdigit():
                    low = float(val)
                    domain = expression.AND([domain, [('list_price', '>=', low)]])
        # Filter: Amenities
        selected_amenities = request.httprequest.args.getlist('amenities')
        if selected_amenities:
            amenity_ids = [int(a) for a in selected_amenities if a.isdigit()]
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

    def _shop_lookup_products(self, attrib_set, options, post, search, website):
        """
        Overrides product lookup to filter strictly by properties.
        """
        fuzzy_search_term, product_count, search_result = super(CustomWebsiteSale, self)._shop_lookup_products(attrib_set, options, post, search, website)
        
        # Filter search results to properties only
        search_result = search_result.filtered(lambda p: p.is_property)
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
        Overrides the shop route to apply Property Details domain filters 
        (Listing Type, Property Type, Beds, Baths, Price Range, Location, Amenities)
        and pass the exact matching property recordset to the template.
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
        args = request.httprequest.args
        params = request.params
        # 1. Gather all input values from GET/POST request
        search_kw = search or args.get('search') or params.get('search') or ''
        location_val = args.get('location') or params.get('location') or ''
        listing_val = args.get('listing') or params.get('listing') or ''
        type_val = args.get('type') or params.get('type') or ''
        beds_val = args.get('beds') or params.get('beds') or ''
        baths_val = args.get('baths') or params.get('baths') or ''
        price_range = args.get('price_range') or params.get('price_range') or ''
        sort_val = args.get('sort') or params.get('sort') or 'newest'
        per_page_val = args.get('per_page') or params.get('per_page') or '12'
        selected_amenities = request.httprequest.args.getlist('amenities')
        # 2. Build property filter domain matching Property Details fields
        domain = [('is_property', '=', True), ('website_published', '=', True)]
        # Keyword search across name, location, property_type
        if search_kw and search_kw.strip():
            kw = search_kw.strip()
            domain = expression.AND([domain, [
                '|', '|',
                ('name', 'ilike', kw),
                ('location', 'ilike', kw),
                ('property_type', 'ilike', kw)
            ]])
        # Listing type ('rent' or 'sale')
        if listing_val and listing_val.strip():
            domain = expression.AND([domain, [('listing_type', '=', listing_val.strip())]])
        # Location
        if location_val and location_val.strip():
            domain = expression.AND([domain, [('location', 'ilike', location_val.strip())]])
        # Property type ('house', 'villa', 'apartment', 'commercial', 'studio', 'office')
        if type_val and type_val.strip():
            domain = expression.AND([domain, [('property_type', '=', type_val.strip())]])
        # Bedrooms
        if beds_val and str(beds_val).isdigit():
            b = int(beds_val)
            if b >= 4:
                domain = expression.AND([domain, [('bed', '>=', 4)]])
            else:
                domain = expression.AND([domain, [('bed', '=', b)]])
        # Bathrooms
        if baths_val and str(baths_val).isdigit():
            b = int(baths_val)
            if b >= 3:
                domain = expression.AND([domain, [('bath', '>=', 3)]])
            else:
                domain = expression.AND([domain, [('bath', '=', b)]])
        # Price range
        if price_range:
            if '-' in price_range:
                parts = price_range.split('-')
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    low, high = float(parts[0]), float(parts[1])
                    domain = expression.AND([domain, [
                        ('list_price', '>=', low),
                        ('list_price', '<=', high)
                    ]])
            elif '+' in price_range:
                val = price_range.replace('+', '').strip()
                if val.isdigit():
                    low = float(val)
                    domain = expression.AND([domain, [('list_price', '>=', low)]])
        # Amenities
        if selected_amenities:
            amenity_ids = [int(a) for a in selected_amenities if a.isdigit()]
            for a_id in amenity_ids:
                domain = expression.AND([domain, [('amenity_ids', 'in', a_id)]])
        # 3. Sorting order
        order_by = 'create_date desc, id desc'
        if sort_val == 'price_asc':
            order_by = 'list_price asc, id desc'
        elif sort_val == 'price_desc':
            order_by = 'list_price desc, id desc'
        # 4. Search and pagination
        matching_properties = request.env['product.template'].sudo().search(domain, order=order_by)
        total_count = len(matching_properties)
        limit = int(per_page_val) if (per_page_val and per_page_val.isdigit()) else 12
        page_num = page if page > 1 else 1
        offset = (page_num - 1) * limit
        paginated_properties = matching_properties[offset:offset + limit]
        # 5. Additional context data for sidebar
        all_amenities = request.env['property.amenity'].sudo().search([])
        selected_amenity_ids = [int(a) for a in selected_amenities if a.isdigit()]
        latest_properties = request.env['product.template'].sudo().search([
            ('is_property', '=', True),
            ('website_published', '=', True)
        ], order='create_date desc', limit=6)
        # 6. Update qcontext with exact filtered property recordset
        values.update({
            'total_count': total_count,
            'search_count': total_count,
            'properties': paginated_properties,
            'products': paginated_properties,
            'search': search_kw,
            'location': location_val,
            'filter_type': type_val,
            'listing_type': listing_val or 'sale',
            'filter_beds': beds_val,
            'filter_baths': baths_val,
            'price_range': price_range,
            'per_page': str(limit),
            'sort': sort_val,
            'all_amenities': all_amenities,
            'selected_amenities': selected_amenity_ids,
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

    @http.route('/aboutus', type='http', auth="public", website=True, sitemap=True)
    def about_us_page(self, **kwargs):
        """
        Serves the About Us page directly.
        """
        return request.render('theme_livelo.about_us_page', {})

    @http.route('/pricing', type='http', auth="public", website=True, sitemap=True)
    def pricing_page(self, **kwargs):
        """
        Serves the Pricing page directly.
        """
        return request.render('theme_livelo.pricing_page', {})

