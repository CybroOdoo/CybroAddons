# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Vishnu KP(odoo@cybrosys.com)
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
    """Fields for twitter authentication"""
    _inherit = "res.config.settings"

    consumer_key = fields.Char(string="Consumer Key",
                               help="The Consumer Key provided by Twitter "
                                    "for authentication.",
                               config_parameter='recruitment_twitter.consumer_key')
    consumer_secret = fields.Char(string="Consumer Secret Key",
                                  help="The Consumer Secret Key provided by"
                                       " Twitter for authentication.",
                                  config_parameter='recruitment_twitter.consumer_secret')
    access_token = fields.Char(string="Access Token",
                               help="The Access Token provided by Twitter for"
                                    " authentication.",
                               config_parameter='recruitment_twitter.access_token')
    access_token_secret = fields.Char(string="Access Token Secret",
                                      help="The Access Token Secret provided "
                                           "by Twitter for authentication.",
                                      config_parameter='recruitment_twitter.access_token_secret')
