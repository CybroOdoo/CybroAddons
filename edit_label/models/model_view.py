# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models
from xml.etree import ElementTree
import itertools


class FieldModels(models.Model):
    _inherit = 'ir.ui.view'

    flag = fields.Boolean(default=False)

    @api.model
    def edit_xml_field_label(self, name, view, field, input_field_name, value,
                             field_name):
        views = self.env['ir.ui.view'].search([('model', '=', name),
                                               ('type', '=', view)])
        model_name = self.env['ir.model'].search([('model', '=', name)]).name
        use_lang = self.env.context.get('lang') or 'en_US'
        for view_id in views:
            root = ElementTree.fromstring(view_id.arch)

            for rank in root.iter('label'):
                if rank.get('string') == field:
                    self.flag = True
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
                        'edited_person': self.env.user.id,
                        'date': fields.Datetime.now(),
                        'model': model_name,
                        'old_label': field,
                        'new_label': value,
                    }
                    self.env['label.history'].sudo().create(vals)

            for rank in root.iter('field'):
                if rank.get('string') == field:
                    self.flag = True
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
                        'edited_person': self.env.user.id,
                        'date': fields.Datetime.now(),
                        'model': model_name,
                        'old_label': field,
                        'new_label': value,
                    }
                    self.env['label.history'].sudo().create(vals)

        if self.flag:
            return True

        else:
            try:
                self.env.cr.execute("""
                        UPDATE ir_model_fields SET field_description = '{"%s":"%s"}' WHERE model = '%s' AND name = '%s'
                        """ % (use_lang, value, name, input_field_name))

                #     self.env.cr.execute("""
                #         UPDATE ir_model_fields SET field_description = '%s' WHERE model = '%s' AND name = '%s'
                #         """ % (value, name, field_name))

                vals = {
                    'edited_person': self.env.user.id,
                    'date': fields.Datetime.now(),
                    'model': model_name,
                    'old_label': field,
                    'new_label': value,
                }
                self.env['label.history'].sudo().create(vals)
                self.env.cr.commit()
                self.env['ir.model.fields'].clear_caches()
                return True
            except Exception as e:
                return False
