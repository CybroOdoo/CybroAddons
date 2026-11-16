################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################
from odoo import http
from odoo.fields import Domain
from odoo.http import request


class VoltroProductSnippets(http.Controller):
    """Provide the dynamic content of the Voltro product snippets."""

    @http.route('/theme_voltro/product_arrivals', type='jsonrpc', auth='public',
                website=True, readonly=True)
    def product_arrivals(self):
        """Render the four latest published products for the arrivals snippet."""
        website = request.env.website
        products = request.env['product.template'].search(
            website.sale_product_domain(), order='create_date desc', limit=4)
        wishlist_product_ids = request.env['product.wishlist'].current().product_id.ids
        return request.env['ir.ui.view']._render_template(
            'theme_voltro.arrival_product_show', {
                'products': products,
                'website': website,
                'wishlist_product_ids': wishlist_product_ids,
            })

    @http.route('/theme_voltro/product_categories', type='jsonrpc', auth='public',
                website=True, readonly=True)
    def product_categories(self):
        """Render the root eCommerce categories for the categories snippet."""
        categories = request.env['product.public.category'].search(
            Domain('parent_id', '=', False) & request.env.website.website_domain())
        return request.env['ir.ui.view']._render_template(
            'theme_voltro.product_categories_show', {'categories': categories})
