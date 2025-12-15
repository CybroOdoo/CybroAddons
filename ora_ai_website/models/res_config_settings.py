# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherited to add the Website assistants fields in the settings."""
    _inherit = 'res.config.settings'

    is_website_assistant = fields.Boolean(string='Enable Website Assistant',
                                          config_parameter='ora_ai_website.is_website_assistant',
                                          help='Check this field for enabling '
                                               'Website assistant')
    website_assistant_id = fields.Many2one('ora.ai',
                                           string="Choose Assistant",
                                           config_parameter='ora_ai_website.website_assistant_id',
                                           domain="[('state', '=', 'done')]")
