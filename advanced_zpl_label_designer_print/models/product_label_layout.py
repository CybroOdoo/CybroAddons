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
    """Extend product label printing with ZPL designer templates."""

    _inherit = 'product.label.layout'

    zpl_template_id = fields.Many2one(
        'zpl.label.template',
        string="ZPL Custom Template"
    )

    print_format = fields.Selection(selection_add=[
        ('advanced_zpl_label_designer_print', 'ZPL Label Designer')
    ], ondelete={'advanced_zpl_label_designer_print': 'set default'})

    def process(self):
        """Print product labels using the selected ZPL template when needed."""
        if self.print_format == 'advanced_zpl_label_designer_print':
            if not self.zpl_template_id:
                raise UserError("Please select a ZPL Template before printing.")

            products = self.product_ids
            if not products and self.product_tmpl_ids:
                products = self.product_tmpl_ids.mapped('product_variant_ids')

            if self.zpl_template_id.model_id.model == 'product.template':
                target_ids = self.product_tmpl_ids.ids if self.product_tmpl_ids else self.product_ids.mapped('product_tmpl_id').ids
            else:
                target_ids = products.ids

            return self.env.ref('advanced_zpl_label_designer_print.action_report_zpl_label_instance').report_action(
                self.zpl_template_id,
                data={
                    'zpl_template_id': self.zpl_template_id.id,
                    'product_ids': target_ids,
                    'quantity': self.custom_quantity or 1,
                }
            )

        return super(ProductLabelLayout, self).process()
