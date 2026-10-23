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


class PosConfig(models.Model):
    """Add the table reservation option to pos.config."""
    _inherit = 'pos.config'

    table_reservation = fields.Boolean(
        help="Allow reserving tables from the POS floor plan editor.")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Make the option available in the POS frontend."""
        pos_fields = super()._load_pos_data_fields(config_id)
        # An empty list means "load every field": nothing to add then.
        if pos_fields and 'table_reservation' not in pos_fields:
            pos_fields.append('table_reservation')
        return pos_fields
