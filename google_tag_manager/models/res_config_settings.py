# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Add a new feature in settings google tag manager boolean field and add a
    char field for enter container ID"""

    _inherit = 'res.config.settings'
    _description = 'inherit model res.config.settings and add fields'

    google_tag_manager = (
        fields.Boolean(string="Google Tag Manager", default=False,
                       help="Enable to give access to google tag manager",
                       config_parameter="google_tag_manager.google_tag_manager"))
    container_id = fields.Char(string="Container ID", default=False,
                               help="Container id of google tag manager",
                               config_parameter=
                               "google_tag_manager.container_id")
