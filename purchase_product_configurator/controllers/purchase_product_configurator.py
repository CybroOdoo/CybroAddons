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
from odoo.http import Controller, request, route


class ProductConfiguratorController(Controller):

    @route('/purchase_product_configurator/get_values', type='json', auth='user')
    def get_product_configurator_values(
            self,
            product_template_id,
            quantity,
            currency_id,
            product_uom_id=None,
            company_id=None,
            ptav_ids=None,
            only_main_product=False,
    ):
        """ Return all product information needed for the product configurator.
        """
        if company_id:
            request.update_context(allowed_company_ids=[company_id])
        product_template = request.env['product.template'].browse(product_template_id)
        combination = request.env['product.template.attribute.value']
        if ptav_ids:
            combination = request.env['product.template.attribute.value'].browse(ptav_ids).filtered(
                lambda ptav: ptav.product_tmpl_id.id == product_template_id
            )
            # Set missing attributes (unsaved no_variant attributes, or new attribute on existing product)
            unconfigured_ptals = (
                    product_template.attribute_line_ids - combination.attribute_line_id).filtered(
                lambda ptal: ptal.attribute_id.display_type != 'multi')
            combination += unconfigured_ptals.mapped(
                lambda ptal: ptal.product_template_value_ids._only_active()[:1]
            )
        if not combination:
            combination = product_template._get_first_possible_combination()
        return dict(
            products=[
                dict(
                    **self._get_product_information(
                        product_template,
                        combination,
                        currency_id,
                        quantity=quantity,
                        product_uom_id=product_uom_id
                    ),
                    parent_product_tmpl_ids=[],
                )
            ],
            optional_products=[
                dict(
                    **self._get_product_information(
                        optional_product_template,
                        optional_product_template._get_first_possible_combination(
                            parent_combination=combination
                        ),
                        currency_id,
                        # giving all the ptav of the parent product to get all the exclusions
                        parent_combination=product_template.attribute_line_ids. \
                            product_template_value_ids,
                    ),
                    parent_product_tmpl_ids=[product_template.id],
                ) for optional_product_template in product_template.optional_product_ids
            ] if not only_main_product else []
        )

    @route('/purchase_product_configurator/create_product', type='json', auth='user')
    def purchase_product_configurator_create_product(self, product_template_id, combination):
        """ Create the product when there is a dynamic attribute in the combination.
        """
        product_template = request.env['product.template'].browse(product_template_id)
        combination = request.env['product.template.attribute.value'].browse(combination)
        product = product_template._create_product_variant(combination)
        return product.id

    @route('/purchase_product_configurator/update_combination', type='json', auth='user')
    def purchase_product_configurator_update_combination(
            self,
            product_template_id,
            combination,
            currency_id,
            quantity,
            product_uom_id=None,
            company_id=None,
    ):
        """ Return the updated combination information.
        """
        if company_id:
            request.update_context(allowed_company_ids=[company_id])
        product_template = request.env['product.template'].browse(product_template_id)
        product_uom = request.env['uom.uom'].browse(product_uom_id)
        currency = request.env['res.currency'].browse(currency_id)
        combination = request.env['product.template.attribute.value'].browse(combination)
        product = product_template._get_variant_for_combination(combination)
        return self._get_basic_product_information(
            product or product_template,
            combination,
            quantity=quantity or 0.0,
            uom=product_uom,
            currency=currency,
        )

    @route('/purchase_product_configurator/get_optional_products', type='json', auth='user')
    def purchase_product_configurator_get_optional_products(
            self,
            product_template_id,
            combination,
            parent_combination,
            currency_id,
            company_id=None,
    ):
        """ Return information about optional products for the given `product.template`.
        """
        if company_id:
            request.update_context(allowed_company_ids=[company_id])
        product_template = request.env['product.template'].browse(product_template_id)
        parent_combination = request.env['product.template.attribute.value'].browse(
            parent_combination + combination
        )
        return [
            dict(
                **self._get_product_information(
                    optional_product_template,
                    optional_product_template._get_first_possible_combination(
                        parent_combination=parent_combination
                    ),
                    currency_id,
                    parent_combination=parent_combination
                ),
                parent_product_tmpl_ids=[product_template.id],
            ) for optional_product_template in product_template.optional_product_ids
        ]

    def _get_product_information(
            self,
            product_template,
            combination,
            currency_id,
            quantity=1,
            product_uom_id=None,
            parent_combination=None,
    ):
        """ Return complete information about a product.
        """
        product_uom = request.env['uom.uom'].browse(product_uom_id)
        currency = request.env['res.currency'].browse(currency_id)
        product = product_template._get_variant_for_combination(combination)
        attribute_exclusions = product_template._get_attribute_exclusions(
            parent_combination=parent_combination,
            combination_ids=combination.ids,
        )
        return dict(
            product_tmpl_id=product_template.id,
            **self._get_basic_product_information(
                product or product_template,
                combination,
                quantity=quantity,
                uom=product_uom,
                currency=currency
            ),
            quantity=quantity,
            attribute_lines=[dict(
                id=ptal.id,
                attribute=dict(**ptal.attribute_id.read(['id', 'name', 'display_type'])[0]),
                attribute_values=[
                    dict(
                        **ptav.read(['name', 'html_color', 'image', 'is_custom'])[0],
                    ) for ptav in ptal.product_template_value_ids
                    if ptav.ptav_active or combination and ptav.id in combination.ids
                ],
                selected_attribute_value_ids=combination.filtered(
                    lambda c: ptal in c.attribute_line_id
                ).ids,
                create_variant=ptal.attribute_id.create_variant,
            ) for ptal in product_template.attribute_line_ids],
            exclusions=attribute_exclusions['exclusions'],
            archived_combinations=attribute_exclusions['archived_combinations'],
            parent_exclusions=attribute_exclusions['parent_exclusions'],
        )

    def _get_basic_product_information(self, product_or_template, combination, **kwargs):
        """ Return basic information about a product
        """
        basic_information = dict(
            **product_or_template.read(['description_sale', 'display_name'])[0]
        )
        # If the product is a template, check the combination to compute the name to take dynamic
        # and no_variant attributes into account. Also, drop the id which was auto-included by the
        # search but isn't relevant since it is supposed to be the id of a `product.product` record.
        if not product_or_template.is_product_variant:
            basic_information['id'] = False
            combination_name = combination._get_combination_name()
            if combination_name:
                basic_information.update(
                    display_name=f"{basic_information['display_name']} ({combination_name})"
                )
        return dict(
            **basic_information,
            price=product_or_template.standard_price
        )
