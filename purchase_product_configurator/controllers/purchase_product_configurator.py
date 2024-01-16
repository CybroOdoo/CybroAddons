# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ayisha Sumayya K, Vivek (odoo@cybrosys.com)
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
from odoo import http
from odoo.http import request


class ProductConfiguratorController(http.Controller):
    """
    Controller for handling product configuration in the purchase module.
    """
    @http.route(['/purchase_product_configurator/configure'], type='json',
                auth="user", methods=['POST'])
    def configure(self, product_template_id, pricelist_id, **kw):
        """
        Configure a product with the specified template and pricelist.
        """
        add_qty = float(kw.get('add_qty', 1))
        product_template = request.env['product.template'].browse(
            int(product_template_id))
        pricelist = self._get_pricelist(pricelist_id)
        product_combination = False
        attribute_value_ids = set(
            kw.get('product_template_attribute_value_ids', []))
        attribute_value_ids |= set(
            kw.get('product_no_variant_attribute_value_ids', []))
        if attribute_value_ids:
            product_combination = request.env[
                'product.template.attribute.value'].browse(attribute_value_ids)
        if pricelist:
            product_template = product_template.with_context(
                pricelist=pricelist.id, partner=request.env.user.partner_id)
        return request.env['ir.ui.view']._render_template(
            "purchase_product_configurator.configure",
            {
                'product': product_template,
                'pricelist': pricelist,
                'add_qty': add_qty,
                'product_combination': product_combination
            },
        )

    @http.route(['/purchase_product_configurator/show_advanced_configurator'],
                type='json', auth="user", methods=['POST'])
    def show_advanced_configurator(self, product_id, variant_values,
                                   pricelist_id, **kw):
        """
        Show the advanced configurator for a product with the specified ID,
        variant values, and pricelist.
        """
        pricelist = self._get_pricelist(pricelist_id)
        return self._show_advanced_configurator(product_id, variant_values,
                                                pricelist, False, **kw)

    @http.route(['/purchase_product_configurator/optional_product_items'],
                type='json', auth="user", methods=['POST'])
    def optional_product_items(self, product_id, pricelist_id, **kw):
        """
        Get the optional product items for the specified product ID and
        pricelist.
        """
        pricelist = self._get_pricelist(pricelist_id)
        return self._optional_product_items(product_id, pricelist, **kw)

    def _optional_product_items(self, product_id, pricelist, **kw):
        """
        Helper method to get the optional product items for the specified
        product ID and pricelist.
        """
        add_qty = float(kw.get('add_qty', 1))
        product = request.env['product.product'].browse(int(product_id))
        parent_combination = product.product_template_attribute_value_ids
        if product.env.context.get('no_variant_attribute_values'):
            parent_combination |= product.env.context.get(
                'no_variant_attribute_values')
        return request.env['ir.ui.view']._render_template(
            "purchase_product_configurator.optional_product_items", {
                'product': product,
                'parent_name': product.name,
                'parent_combination': parent_combination,
                'pricelist': pricelist,
                'add_qty': add_qty,
            })

    def _show_advanced_configurator(self, product_id, variant_values, pricelist,
                                    handle_stock, **kw):
        """
        Helper method to show the advanced configurator for a product with the
        specified ID, variant values, pricelist, and other parameters.
        """
        product = request.env['product.product'].browse(int(product_id))
        combination = request.env['product.template.attribute.value'].browse(
            variant_values)
        add_qty = float(kw.get('add_qty', 1))

        no_variant_attribute_values = combination.filtered(
            lambda
                product_template_attribute_value:
            product_template_attribute_value.attribute_id.
            create_variant == 'no_variant'
        )
        if no_variant_attribute_values:
            product = product.with_context(
                no_variant_attribute_values=no_variant_attribute_values)
        return request.env['ir.ui.view']._render_template(
            "purchase_product_configurator.purchase_optional_products_modal", {
                'product': product,
                'combination': combination,
                'add_qty': add_qty,
                'parent_name': product.name,
                'variant_values': variant_values,
                'pricelist': pricelist,
                'handle_stock': handle_stock,
                'already_configured': kw.get("already_configured", False),
                'mode': kw.get('mode', 'add'),
                'product_custom_attribute_values': kw.get(
                    'product_custom_attribute_values', None)
            })

    def _get_pricelist(self, pricelist_id, pricelist_fallback=False):
        """
        Helper method to get the pricelist based on the specified pricelist ID.
        """
        return request.env['product.pricelist'].browse(int(pricelist_id or 0))
