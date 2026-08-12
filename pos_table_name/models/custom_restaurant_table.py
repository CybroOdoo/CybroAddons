# -*- coding: utf-8 -*-
################################################################################
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
################################################################################
from odoo import api, fields, models


class RestaurantTable(models.Model):
    """
    Model inheritance to add alphanumeric custom table name capabilities 
    to the restaurant tables in POS.
    """
    _inherit = 'restaurant.table'

    custom_table_name = fields.Char(string='Table Name', help='Alphanumeric table identifier (e.g., A1, VIP-1, 101)',
                             copy=False)

    @api.model
    def _load_pos_data_fields(self, config):
        """
        Extends the list of fields loaded by the Point of Sale to include 
        the newly added custom_table_name.
        """
        fields_name = super()._load_pos_data_fields(config)
        if 'custom_table_name' not in fields:
            fields_name.append('custom_table_name')
        return fields_name

    @api.depends('custom_table_name', 'floor_id', 'table_number')
    def _compute_display_name(self):
        """
        Compute the display name for the restaurant table using the custom 
        table name if available, otherwise fallback to the table number.
        """
        for table in self:
            determined_name = table.custom_table_name or str(table.table_number)
            if table.floor_id:
                table.display_name = f"{table.floor_id.name}, {determined_name}"
            else:
                table.display_name = determined_name

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to automatically set the custom table name 
        to the generated table number if no custom name is explicitly provided.
        """
        for vals in vals_list:
            floor_id = vals.get('floor_id')

            if not vals.get('table_number'):
                domain = [('floor_id', '=', floor_id)] if floor_id else []
                last = self.search(domain, order='table_number desc', limit=1)
                vals['table_number'] = (last.table_number + 1) if last else 1

            if not vals.get('custom_table_name'):
                vals['custom_table_name'] = str(vals['table_number'])

        return super().create(vals_list)

    def write(self, vals):
        """
        Override the write method to update the custom table name corresponding 
        to the table number change, provided the name is presently tracking the number.
        """
        if 'table_number' in vals and 'custom_table_name' not in vals:
            for table_rec in self:
                if table_rec.custom_table_name == str(table_rec.table_number):
                    vals['custom_table_name'] = str(vals['table_number'])
                    break
        return super().write(vals)
