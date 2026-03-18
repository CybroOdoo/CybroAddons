# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import re
from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.cart import Cart


class WebsiteProductCustomization(Cart):
    """Extension of Odoo's Cart controller to support custom product design
       handling during website cart operations.
    """

    @http.route(route='/shop/cart/add', type='jsonrpc', auth='public',
                methods=['POST'], website=True, sitemap=False)
    def add_to_cart(self, product_id, quantity=1.0, design_image=None, **kwargs):
        """Override of the default add_to_cart route to include support for
        custom product design images."""
        
        # Call original controller logic
        res = super(WebsiteProductCustomization, self).add_to_cart(
            product_id=int(product_id) if product_id else None,
            add_qty=float(quantity) if quantity else 1.0,
            **kwargs
        )

        # Get the order. Try multiple ways to be safe across Odoo versions.
        order = None
        if hasattr(request, 'website') and hasattr(request.website, 'sale_get_order'):
            order = request.website.sale_get_order()
        
        if not order and request.session.get('sale_order_id'):
            order = request.env['sale.order'].sudo().browse(request.session.get('sale_order_id'))
            
        if not order:
             return res

        if design_image:
            # Remove base64 header prefix if present
            image_base64 = re.sub(r'^data:image/\w+;base64,', '', design_image)
            
            # Find the line just added/updated.
            # Look for lines for this product, sorted by latest update.
            line = order.order_line.filtered(lambda l: l.product_id.id == int(product_id))
            if line:
                last_line = line.sorted(key='write_date', reverse=True)[0]
                last_line.write({
                    'product_design': image_base64,
                    'is_customized_product': True,
                })

        return res
