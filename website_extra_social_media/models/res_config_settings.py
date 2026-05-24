# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC
#    LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit res.config.settings to manage extra social media links."""
    _inherit = 'res.config.settings'

    whatsapp_link = fields.Char(string='WhatsApp Number',
                                config_parameter='website_extra_social_media.whatsapp_link',
                                help='Add your WhatsApp number.')
    instagram_link = fields.Char(string='Instagram',
                                 config_parameter='website_extra_social_media.instagram_link',
                                 help='Add your Instagram account link.')
    github_link = fields.Char(string='GitHub',
                              config_parameter='website_extra_social_media.github_link',
                              help='Add your GitHub account link.')
    youtube_link = fields.Char(string='YouTube',
                               config_parameter='website_extra_social_media.youtube_link',
                               help='Add your YouTube account link.')
    google_plus_link = fields.Char(string='Google Plus',
                                   config_parameter='website_extra_social_media.google_plus_link',
                                   help='Add your Google Plus account link.')
    snapchat_link = fields.Char(string='Snapchat',
                                config_parameter='website_extra_social_media.snapchat_link',
                                help='Add your Snapchat account link.')
    flickr_link = fields.Char(string='Flickr',
                              config_parameter='website_extra_social_media.flickr_link',
                              help='Add your Flickr account link.')
    quora_link = fields.Char(string='Quora',
                             config_parameter='website_extra_social_media.quora_link',
                             help='Add your Quora account link.')
    pinterest_link = fields.Char(string='Pinterest',
                                 config_parameter='website_extra_social_media.pinterest_link',
                                 help='Add your Pinterest account link.')
    dribbble_link = fields.Char(string='Dribbble',
                               config_parameter='website_extra_social_media.dribbble_link',
                               help='Add your Dribbble account link.')
    tumblr_link = fields.Char(string='Tumblr',
                              config_parameter='website_extra_social_media.tumblr_link',
                              help='Add your Tumblr account link.')

    def get_social_media_values(self):
        """Return configured social media links."""
        params = self.env['ir.config_parameter'].sudo()
        social_fields = [
            'instagram', 'whatsapp', 'github', 'youtube', 'google_plus',
            'snapchat', 'flickr', 'quora', 'pinterest', 'dribbble', 'tumblr'
        ]
        return {
            field: params.get_param(f'website_extra_social_media.{field}_link')
            for field in social_fields
        }
