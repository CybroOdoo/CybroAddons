# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Inherits the class sale.order.line for adding the fields for
    secondary uom and the secondary uom Quantity"""
    _inherit = 'sale.order.line'

    secondary_uom_ids = fields.Many2many(
        'uom.uom',
        string="Secondary Uom Ids",
        compute='_compute_secondary_uom_ids',
        help="For fetching all the secondary uom's"
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
        help="The field to check whether the selected uom is secondary "
             "and if yes then make the field readonly"
    )

    @api.depends('product_id', 'product_template_id')
    def _compute_is_secondary_readonly(self):
        """Compute whether secondary UoM fields should be active.
        Uses depends instead of onchange so it always fires — including on
        record load, not only on UI interaction."""
        for rec in self:
            rec.is_secondary_readonly = (
                rec.product_id.is_need_secondary_uom
                or rec.product_template_id.is_need_secondary_uom
            )


    @api.onchange('product_template_id', 'product_id')
    def _onchange_is_secondary_readonly(self):
        """Onchange companion to _compute_is_secondary_readonly."""
        self.is_secondary_readonly = (
            self.product_id.is_need_secondary_uom
            or self.product_template_id.is_need_secondary_uom
        )

    @api.depends('product_id', 'product_template_id')
    def _compute_secondary_uom_ids(self):
        """Compute the list of available secondary UoMs for the sale line.

        Priority:
          1. If the product is a variant with its own secondary UOMs → use those.
          2. Else if the template has secondary UOMs → use those.
          3. Otherwise → empty list.

        Previously this only looked at product_id.secondary_uom_ids and
        completely ignored the template-level UOMs when no variant-level ones
        were set, causing the dropdown to be empty for simple (non-variant)
        products.
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
        """Compute the default secondary UoM for the sale line.

        Fixes:
          - Was using rec.write() inside a compute, which causes recursion /
            dirty-write issues. Replaced with direct field assignment.
          - Was writing secondary_uom_ids (a computed field) via write()
            inside this compute — removed that; _compute_secondary_uom_ids
            handles it on its own dependency chain.
          - Falls back to template UoM when product has no variant UoM set.
          - Assigns False (empty) instead of leaving the field with a stale
            value when no product is selected.
        """
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
        """Recompute product_uom_qty from the secondary UoM quantity and ratio.

        Fixes:
          - primary_uom_ratio was accessed with [0] without checking if the
            list is empty, causing an IndexError when no matching line exists.
          - all_uom was built but the guard `if self.secondary_product_uom_id.id
            in all_uom` was redundant — the domain search already filters for
            exactly that UOM. Simplified.
          - product_uom_readonly does not exist as a standard field on
            sale.order.line; removed to avoid AttributeError.
        """
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