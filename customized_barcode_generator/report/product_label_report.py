# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models


class ProductLabelLayout(models.TransientModel):
    """Extends the product label layout wizard to inject cost_in_code
    into each label dict so it can be rendered in the label templates."""
    _inherit = 'product.label.layout'

    def _prepare_label_values(self, product, barcode_value, copies,
                              packaging, secondary_text=''):
        values = super()._prepare_label_values(
            product, barcode_value, copies, packaging,
            secondary_text=secondary_text)
        # Add cost_in_code to the label dict so it can be rendered in
        # the template. cost_in_code is a computed field on
        # product.template that encodes the standard_price using a
        # configurable character mapping.
        tmpl = product.product_tmpl_id if product.is_product_variant else product
        values['cost_in_code'] = tmpl.cost_in_code or ''
        show_ref = self.env['ir.config_parameter'].sudo().get_bool(
            'customized_barcode_generator.require_ref')
        values['cost_code_reference'] = values['reference'] if show_ref else ''
        return values
