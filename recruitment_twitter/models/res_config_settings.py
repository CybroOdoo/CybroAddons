# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies @cybrosys(odoo@cybrosys.com)
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


class TwittterConfig(models.TransientModel):
    """Fields for twitter authentication"""
    _inherit = "res.config.settings"

    consumer_key = fields.Char("Consumer Key",
                               config_parameter='recruitment_twitter.consumer_key')
    consumer_secret = fields.Char("Consumer Secret Key",
                                  config_parameter='recruitment_twitter.consumer_secret')
    access_token = fields.Char("Access Token",
                               config_parameter='recruitment_twitter.access_token')
    access_token_secret = fields.Char("Access Token Secret",
                                      config_parameter='recruitment_twitter.access_token_secret')
