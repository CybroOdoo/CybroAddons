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
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    """Inherited the product label layout wizard for adding new feature
     Dynamic templates"""
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[('dynamic_template', 'Dynamic Template')],
        ondelete={'dynamic_template': 'set default'},
        help="Added new selection for choosing dynamic template")
    dynamic_template_id = fields.Many2one(
        'dynamic.template',
        help="Select the required template",
    )
    dynamic_field_ids = fields.Many2many(
        'dynamic.fields',
        'dynamic_field_rel',
        help='Relation to dynamic fields',
    )

    @api.onchange('dynamic_template_id')
    def _onchange_dynamic_template_id(self):
        """Passing the values from the template to wizard"""
        self.dynamic_field_ids = self.dynamic_template_id.dynamic_field_ids

    def _prepare_report_data(self):
        """Passing the data to template"""
        if self.print_format == 'dynamic_template':
            xml_id = (
                'dynamic_product_label_print.'
                'product_label_layout_form_dynamic'
            )
            active_model = ''
            if self.product_tmpl_ids:
                products = self.product_tmpl_ids.ids
                active_model = 'product.template'
            elif self.product_ids:
                products = self.product_ids.ids
                active_model = 'product.product'
            else:
                products = []

            fields_to_use = (
                self.dynamic_field_ids
                or (self.dynamic_template_id
                    and self.dynamic_template_id.dynamic_field_ids)
                or []
            )
            dynamic_dict = []
            for i in fields_to_use:
                if i.fd_name_id and i.fd_name_id.name:
                    fname = i.fd_name_id.name
                    if self.product_ids:
                        read_res = self.product_ids.read([fname])
                    elif self.product_tmpl_ids:
                        read_res = self.product_tmpl_ids.read([fname])
                    else:
                        read_res = []
                    dynamic_dict.append({
                        'fname': fname,
                        'fields': read_res,
                        'size': i.size or '14',
                        'color': i.color or '#000000',
                    })

            dynamic_field_ids = [dynamic_dict] if dynamic_dict else []
            bc_width = (
                self.dynamic_template_id.bc_width
                if (self.dynamic_template_id and self.dynamic_template_id.bc_width)
                else 30
            )
            bc_height = (
                self.dynamic_template_id.bc_height
                if (self.dynamic_template_id and self.dynamic_template_id.bc_height)
                else 15
            )
            data = {
                'active_model': active_model,
                'quantity_by_product': {
                    p: self.custom_quantity for p in products
                },
                'layout_wizard': (
                    self.dynamic_template_id.id
                    if self.dynamic_template_id else False
                ),
                'bc_width': bc_width,
                'bc_height': bc_height,
                'dynamic_field_ids': dynamic_field_ids,
            }
            return xml_id, data
        return super()._prepare_report_data()

    def process(self):
        """Returning the report action process for printing the label"""
        self.ensure_one()
        if self.print_format == 'dynamic_template':
            xml_id, data = self._prepare_report_data()
            if not xml_id:
                raise UserError(_(
                    'Unable to find report template for %s format',
                    self.print_format
                ))
            report_action = self.env.ref(xml_id).report_action(
                None, data=data, config=False
            )
            report_action.update({'close_on_report_download': True})
            return report_action
        return super().process()
