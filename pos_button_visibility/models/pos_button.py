# -*- coding: utf-8 -*-
###############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class PosButtons(models.Model):
    """Model to store POS button configuration."""
    _name = 'pos.button'
    _description = "POS Buttons"

    name = fields.Char(string="Name", help="Name of the POS button.")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Return list of fields to load into POS."""
        return ['id', 'name']

    @api.model
    def _load_pos_data_domain(self, data):
        """Return domain for loading POS button data."""
        return []

    @api.model
    def _load_pos_data_search_read(self, data, config_id=False):
        """
        This is the method called by POS to load data.
        """
        domain = self._load_pos_data_domain(data)
        if domain is False:
            return []
        field_names = self._load_pos_data_fields(config_id)
        return self.search_read(domain, field_names, load=False)
