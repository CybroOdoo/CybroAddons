# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Mruthul Raj (odoo@cybrosys.com)
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
from odoo import api, fields, models
from xml.etree import ElementTree


class FieldModels(models.Model):
    """Extends `ir.ui.view` to facilitate label modification in XML fields."""
    _inherit = 'ir.ui.view'

    @api.model
    def edit_xml_field_label(self, name, view, field, input_field_name, value,
                             field_name):
        """Edit the XML field label.
        Args:
        - name: Model name.
        - view: Type of view (e.g., 'form', 'tree').
        - field: Field name to modify.
        - input_field_name: Input field name.
        - value: New label value.
        - field_name: Field name in the view.
        Returns:
        - True if label is edited successfully, False otherwise."""
        views = self.env['ir.ui.view'].search([('model', '=', name),
                                               ('type', '=', view)])
        model_name = self.env['ir.model'].search([('model', '=', name)]).name
        use_lang = self.env.context.get('lang') or 'en_US'
        flag = False
        for view_id in views:
            root = ElementTree.fromstring(view_id.arch)
            for rank in root.iter('label'):
                if rank.get('string') == field_name:
                    if rank.get('nolabel'):
                        preceding_div_labels = root.findall(".//label[@for='" + field_name + "']")
                        for label_tag in preceding_div_labels:
                            label_tag.set('string', value)
                    rank.set('string', value)
                    vals = ElementTree.tostring(root, encoding='unicode')
                    final_view = self.env['ir.ui.view'].sudo().search(
                        [('model', '=', name),
                         ('type', '=', view),
                         ('xml_id', '=', view_id.xml_id),
                         ])
                    for num in final_view.filtered(
                            lambda l: l.xml_id == view_id.xml_id):
                        num.arch = vals
                    vals = {
                        'user_id': self.env.user.id,
                        'date': fields.Datetime.now(),
                        'model': model_name,
                        'old_label': field,
                        'new_label': value,
                    }
                    self.env['label.history'].sudo().create(vals)
                    flag = True
            for rank in root.iter('field'):
                if rank.get('name') == field_name:
                    if rank.get('nolabel'):
                        preceding_div_labels = root.findall(".//label[@for='" + field_name + "']")
                        for label_tag in preceding_div_labels:
                            label_tag.set('string', value)
                    rank.set('string', value)
                    vals = ElementTree.tostring(root, encoding='unicode')
                    final_view = self.env['ir.ui.view'].sudo().search(
                        [('model', '=', name),
                         ('type', '=', view),
                         ('xml_id', '=', view_id.xml_id)])
                    for num in final_view.filtered(
                            lambda l: l.xml_id == view_id.xml_id):
                        num.arch = vals
                    vals = {
                        'user_id': self.env.user.id,
                        'date': fields.Datetime.now(),
                        'model': model_name,
                        'old_label': field,
                        'new_label': value,
                    }
                    self.env['label.history'].sudo().create(vals)
                    flag = True
        if flag:
            return True
        else:
            try:
                self.env.cr.execute("""
                        UPDATE ir_model_fields SET field_description = '{"%s":"%s"}' WHERE model = '%s' AND name = '%s'
                        """ % (use_lang, value, name, input_field_name))
                vals = {
                    'user_id': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'model': model_name,
                    'old_label': field,
                    'new_label': value,
                }
                self.env['label.history'].sudo().create(vals)
                self.env.cr.commit()
                self.env['ir.model.fields']._fields.clear_cache(
                    self.env['ir.model.fields'])
                return True
            except Exception as e:
                return False
