# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Anfas Faisal K (odoo@cybrosys.info)
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
from odoo.http import request

from odoo.addons.website_sale_product_configurator.controllers.main import \
    WebsiteSaleProductConfiguratorController


class WebsiteProductVariant(WebsiteSaleProductConfiguratorController):
    """
    This class extends the WebsiteVariantSale controller to handle the submission
    of optional product modals, ensuring that the Unit of Measure (UOM) is included
    in the cart update operations.
    """
    @http.route(
        '/sale_product_configurator/show_advanced_configurator',
        type='json', auth='public', methods=['POST'], website=True,
    )
    def show_advanced_configurator(
            self, product_id, variant_values, add_qty=1,
            force_dialog=False,
            **kw,
    ):
        """
        This method handles the request to display the advanced product
        configurator, which allows users to configure product variants and
        optional products. It checks if there are any optional products
        that can be added to the cart, and if the product has variants
        or is already configured.
        """
        product = request.env['product.product'].browse(int(product_id))
        product_template = product.product_tmpl_id
        combination = request.env['product.template.attribute.value'].browse(
            variant_values)
        has_optional_products = product.optional_product_ids.filtered(
            lambda p: p._is_add_to_cart_possible(combination)
                      and (
                              not request.website.prevent_zero_price_sale or p._get_contextual_price())
        )
        already_configured = bool(combination)
        if not force_dialog and not has_optional_products and (
                product.product_variant_count <= 1 or already_configured
        ):
            # The modal is not shown if there are no optional products and
            # the main product either has no variants or is already configured
            return False

        add_qty = float(add_qty)
        combination_info = product_template._get_combination_info(
            combination=combination,
            product_id=product.id,
            add_qty=add_qty,
        )
        uom_id_session = request.session['uom_id']

        if uom_id_session:
            uom_id = request.env['uom.uom'].browse(int(uom_id_session))
            product = request.env['product.product'].sudo().browse(product_id)
            default_uom_qty = uom_id._compute_quantity(1, product.uom_id)
            updated_price = combination_info['list_price'] * default_uom_qty
            combination_info.update({'price': updated_price})

        return request.env['ir.ui.view']._render_template(
            'website_sale_product_configurator.optional_products_modal',
            {
                'product': product,
                'product_template': product_template,
                'combination': combination,
                'combination_info': combination_info,
                'add_qty': add_qty,
                'parent_name': product.name,
                'variant_values': variant_values,
                'already_configured': already_configured,
                'mode': kw.get('mode', 'add'),
                'product_custom_attribute_values': kw.get(
                    'product_custom_attribute_values', None),
                'no_attribute': kw.get('no_attribute', False),
                'custom_attribute': kw.get('custom_attribute', False),
            }
        )
