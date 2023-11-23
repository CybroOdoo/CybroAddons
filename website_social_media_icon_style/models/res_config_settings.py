# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Muhsina V (<https://www.cybrosys.com>)
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
    """ Inhering to Add fields to enable social media sharing and styles"""
    _inherit = 'res.config.settings'

    enable_social_media_sharing_style = fields.Boolean(
        string='Product Social Media Sharing',
        config_parameter='website_social_media_icon_style.enable',
        help="Enable social media share button styling feature.")
    icon_style = fields.Selection([('style1', 'ElegantCircle'),
                                   ('style2', 'ClassicCircle'),
                                   ('style3', 'DynamicHover'),
                                   ('style4', 'VividSpinner'),
                                   ('style5', 'VibrantCircle'),
                                   ('style6', 'IconRotate'),
                                   ('style7', 'SquareBackground'),
                                   ('style8', 'SubtleHoverSquare'),
                                   ('style9', 'GradientRotate'),
                                   ('style10', 'RotateLargeIcon'),
                                   ('style11', 'IconWithName')],
                                  string="Icon Style",
                                  config_parameter='website_social_media_icon_style.icon_style',
                                  help="Choose the style of the icon for "
                                       "social media buttons.")
    facebook_icon = fields.Boolean(string="Facebook",
                                   config_parameter='website_social_media_icon_style.facebook'
                                   , help="Enable or disable the Facebook icon"
                                          " for social media sharing.")
    whatsapp_icon = fields.Boolean(string="WhatsApp",
                                   config_parameter='website_social_media_icon_style.whatsapp',
                                   help="Enable or disable the WhatsApp icon "
                                        "for social media sharing.")
    twitter_icon = fields.Boolean(string="Twitter",
                                  config_parameter='website_social_media_icon_style.twitter',
                                  help="Enable or disable the Twitter icon for"
                                       " social media sharing.")
    linkedin_icon = fields.Boolean(string="LinkedIn",
                                   config_parameter='website_social_media_icon_style.linkedin',
                                   help="Enable or disable the LinkedIn icon "
                                        "for social media sharing.")
    email_icon = fields.Boolean(string="E-mail",
                                config_parameter='website_social_media_icon_style.email',
                                help="Enable or disable the E-mail icon for"
                                     " social media sharing.")
    pinterest_icon = fields.Boolean(string="Pinterest",
                                    config_parameter='website_social_media_icon_style.pinterest',
                                    help="Enable or disable the Pinterest "
                                         "icon for social media sharing.")
    reddit_icon = fields.Boolean(string="Reddit",
                                 config_parameter='website_social_media_icon_style.reddit',
                                 help="Enable or disable the Reddit icon for "
                                      "social media sharing.")
    hackernews_icon = fields.Boolean(string="Hacker News",
                                     config_parameter='website_social_media_icon_style.hackernews',
                                     help="Enable or disable the Hacker News "
                                          "icon for social media sharing.")
