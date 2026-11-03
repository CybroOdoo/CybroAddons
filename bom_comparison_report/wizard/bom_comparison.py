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
from odoo.exceptions import ValidationError
from odoo.fields import Command


class BomComparison(models.TransientModel):
    """Compare the cost or the sales price of the components of the bills of
    materials of a product."""
    _name = 'bom.comparison'
    _description = 'BoM Comparison Wizard'

    product_tmpl_id = fields.Many2one(
        'product.template', string='Product', required=True,
        domain="[('bom_ids', '!=', False)]",
        help="Product whose bills of materials are compared")
    bom_ids = fields.Many2many(
        'mrp.bom', string='Bills of Materials', required=True,
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help="Bills of materials to compare, at least two")
    product_unit = fields.Integer(
        string='Number of Products to Produce', default=1, required=True,
        help="The totals are computed for this number of products")
    analysis = fields.Selection(
        [('cost', 'Cost'), ('sale_price', 'Sales Price')],
        string='Analysis Method', required=True, default='cost',
        help="Price of the components the totals are based on")

    @api.model
    def default_get(self, fields):  # pylint: disable=redefined-outer-name
        """Prefill the bills of materials selected in the list."""
        res = super().default_get(fields)
        if self.env.context.get('active_model') == 'mrp.bom':
            boms = self.env['mrp.bom'].browse(
                self.env.context.get('active_ids', []))
            if boms and len(boms.product_tmpl_id) == 1:
                res['product_tmpl_id'] = boms.product_tmpl_id.id
                res['bom_ids'] = [Command.set(boms.ids)]
        return res

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        """Keep only the bills of materials of the selected product."""
        self.bom_ids = self.bom_ids.filtered(
            lambda bom: bom.product_tmpl_id == self.product_tmpl_id)

    @api.constrains('bom_ids')
    def _check_bom_ids(self):
        """At least two bills of materials are compared."""
        for wizard in self:
            if len(wizard.bom_ids) < 2:
                raise ValidationError(self.env._(
                    "Select at least two bills of materials to compare."))

    @api.constrains('product_unit')
    def _check_product_unit(self):
        """The number of products is positive."""
        if any(wizard.product_unit < 1 for wizard in self):
            raise ValidationError(self.env._(
                "The number of products to produce must be at least 1."))

    def _get_bom_unit_price(self, bom):
        """Return the price of the components of one product with the bill
        of materials, in the units of measure of the products."""
        self.ensure_one()
        price_field = ('lst_price' if self.analysis == 'sale_price'
                       else 'standard_price')
        total = sum(
            line.uom_id._compute_quantity(
                line.product_qty, line.product_id.uom_id)
            * line.product_id[price_field]
            for line in bom.bom_line_ids)
        bom_qty = bom.uom_id._compute_quantity(
            bom.product_qty, bom.product_tmpl_id.uom_id)
        return total / bom_qty if bom_qty else 0.0

    def _get_comparison_lines(self):
        """Return the comparison of the bills of materials, cheapest
        first."""
        self.ensure_one()
        lines = []
        for bom in self.bom_ids:
            unit_price = self._get_bom_unit_price(bom)
            lines.append({
                'bom': bom,
                'components': len(bom.bom_line_ids),
                'unit_price': unit_price,
                'total': unit_price * self.product_unit,
            })
        return sorted(lines, key=lambda line: line['total'])

    def action_comparison_report(self):
        """Print the comparison report."""
        self.ensure_one()
        return self.env.ref(
            'bom_comparison_report.bom_comparison_report_action',
        ).report_action(self)
