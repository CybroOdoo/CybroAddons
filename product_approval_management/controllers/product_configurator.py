# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
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
#
###############################################################################
from odoo.addons.sale.controllers.product_configurator import SaleProductConfiguratorController
from odoo.http import request


class SaleProductConfiguratorControllerApproval(SaleProductConfiguratorController):

    def _get_product_information(
        self,
        product_template,
        combination,
        currency,
        pricelist,
        so_date,
        quantity=1,
        product_uom_id=None,
        parent_combination=None,
        **kwargs,
    ):
        """ Override to filter out attribute values that do not lead to any confirmed variant. """
        res = super()._get_product_information(
            product_template,
            combination,
            currency,
            pricelist,
            so_date,
            quantity=quantity,
            product_uom_id=product_uom_id,
            parent_combination=parent_combination,
            **kwargs,
        )

        # Get all confirmed variants for this template
        confirmed_variants = product_template.product_variant_ids.filtered(
            lambda v: v.approve_state == 'confirmed'
        )
        # Get all PTAVs that are part of at least one confirmed variant
        confirmed_ptav_ids = set(confirmed_variants.mapped('product_template_attribute_value_ids').ids)

        for line in res.get('attribute_lines', []):
            if 'attribute_values' in line:
                line['attribute_values'] = [
                    v for v in line['attribute_values']
                    if v['id'] in confirmed_ptav_ids
                ]
        
        # Finally, remove any attribute lines that no longer have any selectable values
        res['attribute_lines'] = [
            line for line in res.get('attribute_lines', [])
            if line.get('attribute_values')
        ]
        
        return res
