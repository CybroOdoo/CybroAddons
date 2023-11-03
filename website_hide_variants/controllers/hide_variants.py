from odoo import http
from odoo.http import request


class HideVariants(http.Controller):
    """Controller for setting routes.Pass all categories and
    category wise products as array to a template"""

    @http.route('/variants/<int:tmpl_id>', type='json', auth='public',website=True, csrf=False)
    def fetch_product_website_hide_variants(self, tmpl_id):
        return request.env['product.product'].sudo().browse(tmpl_id).website_hide_variants
