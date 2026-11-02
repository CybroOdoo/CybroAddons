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


class SaleOrderLine(models.Model):
    """Inherits the class sale.order.line for adding the fields for
    secondary uom and the secondary uom Quantity"""
    _inherit = 'sale.order.line'

    secondary_uom_ids = fields.Many2many(
        'uom.uom',
        string="Secondary Uom Ids",
        compute='_compute_secondary_uom_ids',
        help="For fetching all secondary UoMs"
    )
    secondary_product_uom_id = fields.Many2one(
        'uom.uom',
        string='Secondary UoM',
        compute='_compute_secondary_product_uom',
        store=True,
        readonly=False,
        help="Select the Secondary Uom",
        domain="[('id', 'in', secondary_uom_ids)]"
    )
    secondary_product_uom_qty = fields.Float(
        string='Secondary Quantity',
        help="Select the Secondary Uom Quantity",
        default=1
    )
    is_secondary_readonly = fields.Boolean(
        string="Is Secondary Uom",
        compute='_compute_is_secondary_readonly',
        help="The field to check whether the selected uom is secondary "
             "and if yes then make the field readonly"
    )

    @api.depends('product_id', 'product_template_id')
    def _compute_is_secondary_readonly(self):
        """Compute whether secondary UoM fields should be active."""
        for rec in self:
            rec.is_secondary_readonly = (
                rec.product_id.is_need_secondary_uom
                or rec.product_template_id.is_need_secondary_uom
            )

    @api.depends('product_id', 'product_template_id')
    def _compute_secondary_uom_ids(self):
        """Compute the list of available secondary UoMs for the sale line.

        Priority:
          1. If the product is a variant with its own secondary UOMs -> use those.
          2. Else if the template has secondary UOMs -> use those.
          3. Otherwise -> empty list.
        """
        for rec in self:
            # --- variant-level secondary UOMs (highest priority) ---
            if rec.product_id and rec.product_id.is_need_secondary_uom:
                variant_uoms = rec.product_id.secondary_uom_ids.mapped('secondary_uom_id')
                if variant_uoms:
                    rec.secondary_uom_ids = [fields.Command.set(variant_uoms.ids)]
                    continue

            # --- template-level secondary UOMs (fallback) ---
            if rec.product_template_id and rec.product_template_id.is_need_secondary_uom:
                tmpl_uoms = rec.product_template_id.secondary_uom_ids.mapped('secondary_uom_id')
                if tmpl_uoms:
                    rec.secondary_uom_ids = [fields.Command.set(tmpl_uoms.ids)]
                    continue

            # --- no secondary UOMs available ---
            rec.secondary_uom_ids = [fields.Command.set([])]

    @api.depends('product_id', 'product_template_id')
    def _compute_secondary_product_uom(self):
        """Compute the default secondary UoM for the sale line based on product variant or template."""
        for rec in self:
            # Determine which source to pull UOMs from
            use_variant = (
                rec.product_id
                and rec.product_id.is_need_secondary_uom
                and rec.product_id.secondary_uom_ids
            )
            use_template = (
                not use_variant
                and rec.product_template_id
                and rec.product_template_id.is_need_secondary_uom
                and rec.product_template_id.secondary_uom_ids
            )

            if use_variant:
                rec.secondary_product_uom_id = rec.product_id.uom_id or False
            elif use_template:
                rec.secondary_product_uom_id = rec.product_template_id.uom_id or False
            else:
                rec.secondary_product_uom_id = False

    @api.onchange('secondary_product_uom_id', 'secondary_product_uom_qty')
    def _onchange_secondary_product_uom_id(self):
        """Recompute product_uom_qty from the secondary UoM quantity and ratio."""
        if not self.secondary_product_uom_id:
            return

        domain = [('secondary_uom_id', '=', self.secondary_product_uom_id.id)]

        # Variant with its own secondary UOMs takes priority
        if (self.product_template_id.attribute_line_ids
                and self.product_id.is_need_secondary_uom):
            self.is_secondary_readonly = True
            domain.append(('product_id', '=', self.product_id.id))

        elif self.product_template_id.is_need_secondary_uom:
            self.is_secondary_readonly = True
            domain.append(('product_template_id', '=', self.product_template_id.id))

        if self.is_secondary_readonly:
            uom_line = self.env['secondary.uom.line'].search(domain, limit=1)
            if uom_line and uom_line.secondary_uom_ratio:
                self.product_uom_qty = (
                    uom_line.secondary_uom_ratio * self.secondary_product_uom_qty
                )