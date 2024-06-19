# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ASWIN A K (odoo@cybrosys.com)
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
        string='Fields', domain="[('model_id', '=', model_id)]",
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
        current_record = self.env[info['resModel']].browse(int(info['resId']))
        field_name = info['field']['name']
        configured_model = self.search(
            [('model_id.model', '=', info['field']['relation'])])
        required_data = [[
            {
                'id': field.id,
                'field': field.field_description,
                'field_name': field.name,
                'ttype': field.ttype,
                'value': rec[
                    field.name
                ].display_name if field.ttype == 'many2one' else rec[field.name]
            } for field in configured_model.field_ids
        ] for rec in current_record[field_name]]
        return required_data if required_data != [[]] else False

    @api.model
    def finding_the_data_to_show_tooltip_many2many(self, info):
        """
            Method to find data for tooltips in many2many,
             many2one relationships.

            :param info: Information about the tooltip request.
            :type info: dict
            :return: Data to display in the tooltip.
            :rtype: list or string
        """
        rec_to_show = self.env[info['field']['relation']].browse(
            int(info['related_record_id']))
        configured_model = self.search(
            [('model_id.model', '=', info['field']['relation'])])
        required_data = [
            {
                'id': field.id,
                'field': field.field_description,
                'field_name': field.name,
                'ttype': field.ttype,
                'value': rec_to_show[
                    field.name
                ].display_name if field.ttype == 'many2one' else rec_to_show[field.name]
            }
            for field in configured_model.field_ids]
        if required_data == [] and info['viewMode'] == 'list':
            required_data = rec_to_show.display_name
        return required_data
