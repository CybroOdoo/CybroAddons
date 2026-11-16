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
from odoo import api, fields, models


class RestaurantTable(models.Model):
    """Extend restaurant tables with a customizable POS display alias."""

    _inherit = 'restaurant.table'

    table_alias = fields.Char(
        string='Table Name', 
        help='Flexible alphanumeric label (e.g. VIP-A, Zone-1)',
        copy=False
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Include the custom alias in restaurant table data sent to the POS.

        :param config: The current pos.config record.
        :return: List of fields to be loaded into POS.
        :rtype: list[str]
        """
        pos_fields = super()._load_pos_data_fields(config)
        return pos_fields + ['table_alias'] if 'table_alias' not in pos_fields else pos_fields

    @api.depends('table_alias', 'floor_id', 'table_number')
    def _compute_display_name(self):
        """Build the table display name from its alias or number and floor.

        If no alias exists, use the table number. Append the floor name when
        the table belongs to a floor.
        """
        # Personalized naming convention: Alias @ Floor
        for row in self:
            label = row.table_alias if row.table_alias else str(row.table_number)
            row.display_name = f"{label} @ {row.floor_id.name}" if row.floor_id else label

    @api.model_create_multi
    def create(self, list_vals):
        """Create tables and fill in a missing table number or alias.

        :param list_vals: List of value dictionaries for new records.
        :return: Created restaurant.table record set.
        :rtype: odoo.models.Model
        """
        for data in list_vals:
            if not data.get('table_alias'):
                idx = data.get('table_number')
                if not idx:
                    flr = data.get('floor_id')
                    prev = self.search([('floor_id', '=', flr)], order='table_number desc', limit=1)
                    idx = (prev.table_number + 1) if prev else 1
                    data['table_number'] = idx
                data['table_alias'] = str(idx)
        return super().create(list_vals)
