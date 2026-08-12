# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import models, fields
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    """Extends the standard product label print wizard with an extra
    print format that renders labels through a custom ZPL template."""
    _inherit = 'product.label.layout'

    zpl_template_id = fields.Many2one(
        'zpl.label.template',
        string="ZPL Custom Template"
    )

    print_format = fields.Selection(selection_add=[
        ('zpl_label_designer', 'ZPL Label Designer')
    ], ondelete={'zpl_label_designer': 'set default'})

    def process(self):
        """Build and return the ZPL report action when the ZPL Label
        Designer print format is selected, converting the wizard's
        selected products into the recordset/model expected by the
        chosen ZPL template; otherwise defer to the standard wizard
        behaviour."""
        if self.print_format == 'zpl_label_designer':
            if not self.zpl_template_id:
                raise UserError("Please select a ZPL Template before printing.")

            template_model = self.zpl_template_id.model_id.model
            if template_model == 'product.template':
                products = self.product_tmpl_ids
                if not products and self.product_ids:
                    products = self.product_ids.product_tmpl_id
            elif template_model == 'product.product':
                products = self.product_ids
                if not products and self.product_tmpl_ids:
                    products = self.product_tmpl_ids.mapped('product_variant_ids')
            else:
                raise UserError(
                    "The selected ZPL Template '%s' is not configured for "
                    "Products. Please choose a template whose Model is "
                    "Product or Product Variant." % self.zpl_template_id.name
                )

            return self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance').report_action(
                self.zpl_template_id,
                data={
                    'zpl_template_id': self.zpl_template_id.id,
                    'product_ids': products.ids,
                    'quantity': self.custom_quantity or 1,
                }
            )

        return super(ProductLabelLayout, self).process()
