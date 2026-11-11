# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
import base64

from odoo import api, fields, models


class HoverRelatedFields(models.Model):
    """
        Model for managing hover-related fields and their configurations.
    """
    _name = 'hover.related.fields'
    _description = 'Hover Related Fields'
    _rec_name = 'model_id'
    _unique_model_id = models.Constraint(
        'unique(model_id)',
        'One model should only have one configuration.')

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
        domain="[('id', 'not in', model_ids)]",
        help='Select a model for configuration',
    )
    field_ids = fields.Many2many(
        'ir.model.fields',
        string='Fields', domain="[('model_id', '=', model_id)]",
        help='Fields related to the selected model',
    )
    active = fields.Boolean(
        default=True,
        help='Helps to archive the configurations')

    @api.depends('model_id')
    def _compute_model_ids(self):
        groups = self._read_group([], groupby=['model_id'])
        configured_models = self.env['ir.model'].browse(
            [model.id for (model,) in groups if model])
        for record in self:
            record.model_ids = configured_models

    @api.model
    def _get_tooltip_value(self, record, field):
        """
            Return the value of a configured field in a form that can be
            sent to the client.

            :param record: Record to read the value from.
            :param field: ir.model.fields record describing the field.
            :return: Serializable value for the tooltip.
        """
        value = record[field.name]
        if field.ttype == 'many2one':
            return value.display_name
        if field.ttype in ('binary', 'image'):
            return base64.b64encode(value).decode('utf-8') if value else False
        return value

    @api.model
    def _prepare_tooltip_line(self, record, field):
        """
            Build one tooltip line for the given record and field.
        """
        return {
            'id': field.id,
            'field': field.field_description,
            'field_name': field.name,
            'ttype': field.ttype,
            'value': self._get_tooltip_value(record, field),
        }

    @api.model
    def finding_the_data_to_show_tooltip(self, info):
        """
            Method to find data to display in tooltips based on the provided
            information.

            :param info: Information about the tooltip request.
            :type info: dict
            :return: Data to display in the tooltip.
            :rtype: list
        """
        current_record = self.env[info['resModel']].browse(int(info['resId']))
        field_name = info['field']['name']
        configured_model = self.search(
            [('model_id.model', '=', info['field']['relation'])])
        return [
            self._prepare_tooltip_line(rec, field)
            for field in configured_model.field_ids
            for rec in current_record[field_name]
        ]

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
            self._prepare_tooltip_line(rec_to_show, field)
            for field in configured_model.field_ids
        ]
        if not required_data and info['viewMode'] == 'list':
            return rec_to_show.display_name
        return required_data
