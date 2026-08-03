# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
import json
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Extension of product.template to support product bundle packs."""
    _inherit = 'product.template'

    is_bundle = fields.Boolean(
        string='Is Bundle Pack',
        help='If checked, this product will be treated as a bundle.',
    )
    calc_pack_price = fields.Boolean(
        string='Calculate Pack Price',
        help='If enabled, the sales price will be calculated from bundle items.',
    )
    calc_pack_cost = fields.Boolean(
        string='Calculate Pack Cost Price',
        help='If enabled, the cost price will be calculated from bundle items.',
    )
    bundle_line_ids = fields.One2many(
        'product.bundle.line',
        'bundle_id',
        string='Bundle Items',
        help='List of component products included in this bundle.',
    )
    bundle_contents_info = fields.Text(
        compute='_compute_bundle_contents_info',
        store=True,
        string='Bundle Contents (PoS)',
        help='Simplified JSON of bundle components for PoS display.',
    )

    @api.depends('is_bundle', 'bundle_line_ids', 'bundle_line_ids.product_id',
                 'bundle_line_ids.quantity')
    def _compute_bundle_contents_info(self):
        """Compute a JSON summary of bundle components for PoS display."""
        for template in self:
            if template.is_bundle:
                details = [
                    {
                        'id': line.product_id.id,
                        'name': line.product_id.display_name,
                        'qty': line.quantity,
                        'price': line.product_id.list_price,
                        'uom': line.product_id.uom_id.name or 'Units',
                    }
                    for line in template.bundle_line_ids
                    if line.product_id
                ]
                template.bundle_contents_info = json.dumps(details)
            else:
                template.bundle_contents_info = False

    @api.onchange('bundle_line_ids', 'calc_pack_price', 'calc_pack_cost', 'is_bundle')
    def _onchange_bundle_pack_prices(self):
        """Dynamically calculate price and cost when lines or toggles change."""
        self._update_bundle_prices()

    def _update_bundle_prices(self):
        """Calculate and update list_price and standard_price from bundle lines."""
        for record in self:
            if record.is_bundle:
                updates = {}
                if record.calc_pack_price:
                    updates['list_price'] = sum(
                        line.quantity * line.product_id.list_price
                        for line in record.bundle_line_ids
                    )
                if record.calc_pack_cost:
                    updates['standard_price'] = sum(
                        line.quantity * line.product_id.standard_price
                        for line in record.bundle_line_ids
                    )
                if updates:
                    record.update(updates)

    @api.constrains('is_bundle', 'attribute_line_ids')
    def _check_bundle_variants(self):
        """Ensure bundle products do not have product variants."""
        for template in self:
            if template.is_bundle and template.attribute_line_ids:
                raise ValidationError(
                    "Product bundle packs cannot have variants. "
                    "Please remove all attributes to enable bundle mode."
                )

    def write(self, vals):
        """Ensure prices are updated on write if calculation is enabled.
        Also trigger updates if this product is a component of other bundles.
        """
        res = super(ProductTemplate, self).write(vals)
        # 1. Update this template if it's a bundle and its own pack settings/lines changed
        if any(f in vals for f in ['bundle_line_ids', 'calc_pack_price', 'calc_pack_cost', 'is_bundle']):
            self._update_bundle_prices()
        # 2. If this product's price/cost changed, update all bundles containing it
        if 'list_price' in vals or 'standard_price' in vals:
            # Find all bundle lines that contain this template's variants
            lines = self.env['product.bundle.line'].search([
                ('product_id.product_tmpl_id', 'in', self.ids)
            ])
            bundles = lines.mapped('bundle_id')
            if bundles:
                bundles._update_bundle_prices()
        return res

    def _get_ribbon(self, price_vals=None, auto_assign_ribbons=None, variant=None):
        """Return the 'Pack' ribbon if the product is a bundle."""
        if self.is_bundle:
            return self.env.ref('advanced_product_pack.ribbon_bundle_pack')
        return super()._get_ribbon(
            price_vals=price_vals,
            auto_assign_ribbons=auto_assign_ribbons,
            variant=variant,
        )


class ProductProduct(models.Model):
    """Extension of product.product to expose bundle flag and PoS data for variants."""
    _inherit = 'product.product'

    is_bundle = fields.Boolean(
        related='product_tmpl_id.is_bundle',
        store=True,
    )
    bundle_contents_info = fields.Text(
        related='product_tmpl_id.bundle_contents_info',
        store=True,
    )

    def write(self, vals):
        """Ensure bundles are updated if a specific variant price/cost changes."""
        res = super(ProductProduct, self).write(vals)
        if 'lst_price' in vals or 'standard_price' in vals:
            # Find all bundle lines that contain these specific variants
            lines = self.env['product.bundle.line'].search([
                ('product_id', 'in', self.ids)
            ])
            bundles = lines.mapped('bundle_id')
            if bundles:
                bundles._update_bundle_prices()
        return res
