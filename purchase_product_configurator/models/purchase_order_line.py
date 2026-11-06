# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    """
    Model for representing purchase order lines with additional fields and
    methods.
    Inherits from 'purchase.order.line' model.
    """
    _inherit = 'purchase.order.line'

    product_config_mode = fields.Selection(
        related='product_template_id.product_config_mode',
        depends=['product_template_id'],
        help="Product configuration mode.",
    )
    purchase_product_custom_attribute_value_ids = fields.One2many(
        comodel_name='product.attribute.custom.value',
        inverse_name='purchase_order_line_id',
        string="Custom Values",
        compute='_compute_custom_attribute_values_purchase',
        help="Product custom attribute values.",
        store=True,
        readonly=False,
        precompute=True,
        copy=True,
    )
    product_no_variant_attribute_value_ids = fields.Many2many(
        comodel_name='product.template.attribute.value',
        relation='purchase_order_line_product_template_attribute_value_rel',
        string="Extra Values",
        compute='_compute_no_variant_attribute_values',
        store=True,
        readonly=False,
        precompute=True,
        help="Product no-variant attribute values.",
    )

    @api.depends('product_id')
    def _compute_custom_attribute_values_purchase(self):
        """
        Checks if the product has custom attribute values associated with it,
        and if those values belong to the valid values of the product template.
        """
        for line in self:
            if not line.product_id:
                line.purchase_product_custom_attribute_value_ids = False
                continue
            if not line.purchase_product_custom_attribute_value_ids:
                continue
            valid_values = (
                line.product_id.product_tmpl_id
                .valid_product_template_attribute_line_ids
                .product_template_value_ids
            )
            for attribute in line.purchase_product_custom_attribute_value_ids:
                if (
                    attribute.custom_product_template_attribute_value_id
                    not in valid_values
                ):
                    line.purchase_product_custom_attribute_value_ids -= attribute

    @api.depends('product_id')
    def _compute_no_variant_attribute_values(self):
        """
        Keeps only the no-variant attribute values that belong to this template.
        """
        for line in self:
            if not line.product_id:
                line.product_no_variant_attribute_value_ids = False
                continue
            if not line.product_no_variant_attribute_value_ids:
                continue
            valid_values = (
                line.product_template_id
                .valid_product_template_attribute_line_ids
                .product_template_value_ids
            )
            line.product_no_variant_attribute_value_ids = (
                line.product_no_variant_attribute_value_ids.filtered(
                    lambda ptav: ptav in valid_values
                )
            )
