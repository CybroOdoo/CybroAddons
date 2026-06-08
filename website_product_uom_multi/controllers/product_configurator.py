# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.info)
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
from odoo.http import Controller, request, route
from datetime import datetime
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.product_configurator import WebsiteSaleProductConfiguratorController
from odoo.addons.sale.controllers.product_configurator import SaleProductConfiguratorController


class SaleProductConfiguratorController(SaleProductConfiguratorController, WebsiteSale):
    @http.route(route='/sale/product_configurator/get_values', type='jsonrpc', auth='user')
    def sale_product_configurator_get_values(
            self,
            product_template_id,
            quantity,
            currency_id,
            so_date,
            product_uom_id=None,
            company_id=None,
            pricelist_id=None,
            ptav_ids=None,
            only_main_product=False,
            **kwargs,
    ):
        if company_id:
            request.update_context(allowed_company_ids=[company_id])
        product_template = self._get_product_template(product_template_id)

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
        currency = request.env['res.currency'].browse(currency_id)
        pricelist = request.env['product.pricelist'].browse(pricelist_id)
        so_date = datetime.fromisoformat(so_date)

        return dict(
            products=[
                dict(
                    **self._get_product_information(
                        product_template,
                        combination,
                        currency,
                        pricelist,
                        so_date,
                        quantity=quantity,
                        product_uom_id=product_uom_id,
                        **kwargs,
                    ),
                )
            ],
            optional_products=[
                dict(
                    **self._get_product_information(
                        optional_product_template,
                        optional_product_template._get_first_possible_combination(
                            parent_combination=combination
                        ),
                        currency,
                        pricelist,
                        so_date,
                        # giving all the ptav of the parent product to get all the exclusions
                        parent_combination=product_template.attribute_line_ids. \
                            product_template_value_ids,
                        **kwargs,
                    ),
                    parent_product_tmpl_id=product_template.id,
                ) for optional_product_template in product_template.optional_product_ids if
                self._should_show_product(optional_product_template, combination)
            ] if not only_main_product else [],
            currency_id=currency_id,
        )
