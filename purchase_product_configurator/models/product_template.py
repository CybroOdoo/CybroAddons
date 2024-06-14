# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Unnimaya C O (odoo@cybrosys.com)
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
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _check_company_auto = True

    product_config_mode = fields.Selection(selection=[('configurator',
                                                       "Product Configurator"),
                                                      ('matrix',
                                                       "Order Grid Entry")],
                                           string="Product Mode",
                                           default='configurator',
                                           help="Configurator: choose "
                                                "attribute values to add "
                                                "the matching product variant"
                                                " to the order. "
                                                "\nGrid: add several variants"
                                                " at once from the grid "
                                                "of attribute values")
    optional_product_ids = fields.Many2many(
        comodel_name='product.template',
        relation='product_optional_rel',
        column1='src_id',
        column2='dest_id',
        string="Optional Products",
        help="Optional Products are suggested "
             "whenever the customer hits *Add to Cart* (cross-sell strategy, "
             "e.g. for computers: warranty, software, etc.).",
        check_company=True)

    @api.depends('attribute_line_ids.value_ids.is_custom', 'attribute_line_ids.attribute_id.create_variant')
    def _compute_has_configurable_attributes(self):
        """ A product is considered configurable if:
        - It has dynamic attributes
        - It has any attribute line with at least 2 attribute values configured
        - It has at least one custom attribute value """
        for product in self:
            product.has_configurable_attributes = (
                any(attribute.create_variant == 'dynamic' for attribute in product.attribute_line_ids.attribute_id)
                or any(len(attribute_line_id.value_ids) >= 2 for attribute_line_id in product.attribute_line_ids)
                or any(attribute_value.is_custom for attribute_value in product.attribute_line_ids.value_ids)
            )

    def get_single_product_variant(self):
        """ Method used by the product configurator to check if the product is configurable or not.

        We need to open the product configurator if the product:
        - is configurable (see has_configurable_attributes)
        - has optional products """
        res = super().get_single_product_variant()
        if res.get('product_id', False):
            has_optional_products = False
            for optional_product in self.product_variant_id.optional_product_ids:
                if optional_product.has_dynamic_attributes() or optional_product._get_possible_variants(
                    self.product_variant_id.product_template_attribute_value_ids
                ):
                    has_optional_products = True
                    break
            res.update({
                'has_optional_products': has_optional_products,
            })
        return res
