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
from odoo import models

class PosConfig(models.Model):
    """Preserve custom table aliases when saving a POS floor plan."""

    _inherit = 'pos.config'

    def _save_floor_plan_table(self, table_data, floor, existing_tables):
        """Save a floor-plan table and apply its supplied alias.

        :param table_data: Floor-plan table values received from the POS.
        :param floor: Floor containing the table being saved.
        :param existing_tables: Tables already present on the floor.
        :return: The saved restaurant table record, if one was created.
        """
        table = super()._save_floor_plan_table(table_data, floor, existing_tables)
        if table and 'table_alias' in table_data:
            table.write({'table_alias': table_data['table_alias']})
        return table
