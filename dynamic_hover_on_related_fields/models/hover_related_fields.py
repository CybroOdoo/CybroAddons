# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Rosmy John (odoo@cybrosys.com)
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
import json
from odoo import api, fields, models


class HoverRelatedFields(models.Model):
    """
        Model for managing hover-related fields and their configurations.
    """
    _name = 'hover.related.fields'
    _description = 'Hover Related Fields'
    _rec_name = 'model_id'
    _sql_constraints = [
        ('unique_model_id', 'UNIQUE(model_id)',
         'One model should only have one configuration.')
    ]

    model_ids = fields.Many2many(
        'ir.model',
        'hover_related_models_rel',
        string='Models',
        compute='_compute_model_ids',
        help='Models related to the configuration '
             'for setting domain for model_id',
    )
    model_id = fields.Many2one(
        'ir.model',
        'Model',
        domain="[('id', 'not in', model_ids)]",
        help='Select a model for configuration',
    )
    field_ids = fields.Many2many(
        'ir.model.fields',
        string='Fields',
        domain="[('model_id', '=', model_id)]",
        help='Fields related to the selected model',
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Helps to archive the configurations')

    @api.depends('model_id')
    def _compute_model_ids(self):
        self.model_ids = self.search([]).mapped('model_id')

    @api.model
    def finding_the_data_to_show_tooltip(self, info):
        """
            Method to find data to display in tooltips based on the provided
            information.

            :param info: Information about the tooltip request.
            :type info: dict
            :return: Data to display in the tooltip.
            :rtype: list or bool
        """
        info = json.loads(info)
        required_data = [[]]
        current_record = self.env[info['resModel']].browse(int(info['resId']))
        field_name = info['field']['name']
        if 'relation' in info['field']:
            configured_model = self.search(
                [('model_id.model', '=', info['field']['relation'])])
            if info['field']['formatType'] == 'many2one':
                required_data = [[
                    {
                        'id': field.id,
                        'field': field.field_description,
                        'field_char': field_name,
                        'field_name': field.name,
                        'formatType': info['field']['formatType'],
                        'm2o_value': info['field']['m2o_value'],
                        'ttype': field.ttype,
                        'value': rec[
                            field.name
                        ].display_name if field.ttype == 'many2one' else
                        rec[field.name]
                    } for field in configured_model.field_ids
                ] for rec in current_record[field_name]]
            else:
                required_data = [[
                    {
                        'id': field.id,
                        'field': field.field_description,
                        'field_char': field_name,
                        'field_name': field.name,
                        'formatType': info['field']['formatType'],
                        'ttype': field.ttype,
                        'value': rec[
                            field.name
                        ].display_name if field.ttype == 'many2one' else rec[
                            field.name]
                    } for field in configured_model.field_ids
                ] for rec in current_record[field_name]]
        return required_data if required_data != [[]] else False
