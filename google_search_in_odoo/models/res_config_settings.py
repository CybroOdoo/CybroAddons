# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Yadhu Shankar E (odoo@cybrosys.com)
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


class ResConfigSettings(models.TransientModel):
    """Inherit settings to add Google Search configuration fields."""
    _inherit = 'res.config.settings'

    google_search = fields.Boolean(
        string='Enable Google Search',
        config_parameter='google_search_in_odoo.google_search',
        help="Enable Google search in the systray")
    ser_client_api = fields.Char(
        string="API Key",
        config_parameter='google_search_in_odoo.ser_client_api',
        help="API key for Exa web search")

    @api.model
    def google_search_config(self, input_data):
        """Proxy to res.users.google_search_config."""
        return self.env['res.users'].google_search_config(input_data)
