# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies (<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo import api, models, fields


class IrModelFields(models.Model):
    """Adding a new field to understand the dynamically created fields."""

    _inherit = 'ir.model.fields'

    is_dynamic_field = fields.Boolean(string="Dynamic Field",
                                      help="id created using All In One "
                                           "Dynamic Custom Fields")
    custom_field_id = fields.Many2one('dynamic.fields','Custom Field')

    @api.model
    def create(self, vals):
        record = super().create(vals)
        if vals.get('field_description') and record.custom_field_id:
            record.custom_field_id.write({
                'field_label': vals['field_description']
            })
        return record

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'field_description' in vals and rec.custom_field_id:
                rec.custom_field_id.write({
                    'field_label': vals['field_description']
                })
        return res