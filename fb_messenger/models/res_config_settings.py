# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ansil pv (odoo@cybrosys.com)
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

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    Inheriting fields into settings
    """
    _inherit = 'res.config.settings'

    enable_messenger = fields.Boolean("Enable Messenger",
                                      related="website_id.enable_messenger",
                                      help="Enable for show page id field",
                                      readonly=False)
    fb_id_page = fields.Char("Facebook Page Id",
                             related="website_id.fb_id_page",
                             help="To add facebook page id", readonly=False)
