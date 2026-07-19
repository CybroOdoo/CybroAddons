# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Surya Gayathry T A (odoo@cybrosys.com)
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
    _inherit = 'restaurant.table'

    table_alias = fields.Char(
        string='Table Name', 
        help='Flexible alphanumeric label (e.g. VIP-A, Zone-1)',
        copy=False
    )

    @api.model
    def _load_pos_data_fields(self, config):
        """Extend loaded POS fields to include the custom table alias.

        :param config: The current pos.config record.
        :return: List of fields to be loaded into POS.
        :rtype: list[str]
        """
        # Extend the data loading to include custom aliases
        pos_fields = super()._load_pos_data_fields(config)
        return pos_fields + ['table_alias'] if 'table_alias' not in pos_fields else pos_fields

    @api.depends('table_alias', 'floor_id', 'table_number')
    def _compute_display_name(self):
        """Compute a personalized display name formatted as 'Alias @ Floor'.

        If no alias is specified, falls back to the default table number.
        """
        # Personalized naming convention: Alias @ Floor
        for row in self:
            label = row.table_alias if row.table_alias else str(row.table_number)
            row.display_name = f"{label} @ {row.floor_id.name}" if row.floor_id else label

    @api.model_create_multi
    def create(self, list_vals):
        """Override create to auto-assign a table alias and number if not provided.

        :param list_vals: List of value dictionaries for new records.
        :return: Created restaurant.table record set.
        :rtype: odoo.models.Model
        """
        for data in list_vals:
            # Auto-assign alias from number if missing
            if not data.get('table_alias'):
                idx = data.get('table_number')
                if not idx:
                    flr = data.get('floor_id')
                    prev = self.search([('floor_id', '=', flr)], order='table_number desc', limit=1)
                    idx = (prev.table_number + 1) if prev else 1
                    data['table_number'] = idx
                data['table_alias'] = str(idx)
        return super().create(list_vals)
