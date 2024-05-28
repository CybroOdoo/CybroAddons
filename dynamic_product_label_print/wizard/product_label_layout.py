# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductLabelLayout(models.TransientModel):
    """Inherited the product label layout wizard for adding new feature
     Dynamic templates"""
    _inherit = 'product.label.layout'

    print_format = fields.Selection(
        selection_add=[('dynamic_template', 'Dynamic Template'), ],
        ondelete={'dynamic_template': 'set default'},
        help="Added new selection for choosing dynamic template")
    dynamic_template_id = fields.Many2one('dynamic.template',
                                          help="Select the required template")
    dynamic_field_ids = fields.Many2many('dynamic.fields',
                                         'dynamic_field_rel',
                                         help='Relation to dynamic fields')

    @api.onchange('dynamic_template_id')
    def _onchange_dynamic_template_id(self):
        """Passing the values from the template to wizard"""
        self.dynamic_field_ids = self.dynamic_template_id.dynamic_field_ids

    def _prepare_report_data(self):
        """Passing the datas to template"""
        xml_id, data = super()._prepare_report_data()
        if 'dynamic_template' in self.print_format:
            xml_id = 'dynamic_product_label_print.product_label_layout_form_dynamic'
            active_model = ''
            if self.product_tmpl_ids:
                products = self.product_tmpl_ids.ids
                active_model = 'product.template'
            elif self.product_ids:
                products = self.product_ids.ids
                active_model = 'product.product'
            dynamic_field_ids = []
            if self.product_ids:
                dynamic_dict = [
                    {'fields': self.product_ids.read([i.fd_name_id.name]),
                     'size': i.size,
                     'color': i.color} for i in self.dynamic_field_ids]
            else:
                dynamic_dict = [
                    {'fields': self.product_tmpl_ids.read([i.fd_name_id.name]),
                     'size': i.size,
                     'color': i.color} for i in self.dynamic_field_ids]
            dynamic_field_ids.append(dynamic_dict)
            data = {
                'active_model': active_model,
                'quantity_by_product': {p: self.custom_quantity for p in
                                        products},
                'layout_wizard': self.dynamic_template_id,
                'bc_width': self.dynamic_template_id.bc_width,
                'bc_height': self.dynamic_template_id.bc_height,
                'dynamic_field_ids': dynamic_field_ids,
            }
        return xml_id, data

    def process(self):
        """Returning the report action process for printing the label"""
        action = super(ProductLabelLayout, self).process()
        self.ensure_one()
        xml_id, data = self._prepare_report_data()
        if not xml_id:
            raise UserError(_('Unable to find report template for %s format'))
        report_action = self.env.ref(xml_id).report_action(None, data=data)
        report_action.update({'close_on_report_download': True})
        return action
