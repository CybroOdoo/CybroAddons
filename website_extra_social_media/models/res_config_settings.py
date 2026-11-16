###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
    """Inherit res.config.settings to add extra social media configuration fields."""
    _inherit = 'res.config.settings'

    whatsapp_link = fields.Char(string='WhatsApp Number',
                                config_parameter='website_extra_social_media.whatsapp_link',
                                help='Enter your WhatsApp number.')
    instagram_link = fields.Char(string='Instagram',
                                 config_parameter='website_extra_social_media.instagram_link',
                                 help='Enter your Instagram account URL.')
    github_link = fields.Char(string='GitHub',
                              config_parameter='website_extra_social_media.github_link',
                              help='Enter your GitHub account URL.')
    youtube_link = fields.Char(string='YouTube',
                               config_parameter='website_extra_social_media.youtube_link',
                               help='Enter your YouTube account URL.')
    google_plus_link = fields.Char(string='Google+',
                                   config_parameter='website_extra_social_media.google_plus_link',
                                   help='Enter your Google+ account URL.')
    snapchat_link = fields.Char(string='Snapchat',
                                config_parameter='website_extra_social_media.snapchat_link',
                                help='Enter your Snapchat account URL.')
    flickr_link = fields.Char(string='Flickr',
                              config_parameter='website_extra_social_media.flickr_link',
                              help='Enter your Flickr account URL.')
    quora_link = fields.Char(string='Quora',
                             config_parameter='website_extra_social_media.quora_link',
                             help='Enter your Quora account URL.')
    pinterest_link = fields.Char(string='Pinterest',
                                 config_parameter='website_extra_social_media.pinterest_link',
                                 help='Enter your Pinterest account URL.')
    dribbble_link = fields.Char(string='Dribbble',
                                config_parameter='website_extra_social_media.dribbble_link',
                                help='Enter your Dribbble account URL.')
    tumblr_link = fields.Char(string='Tumblr',
                              config_parameter='website_extra_social_media.tumblr_link',
                              help='Enter your Tumblr account URL.')

    @api.model
    def get_social_media_values(self):
        """Return the configured social links for internal callers."""
        get_param = self.env['ir.config_parameter'].sudo().get_str
        return {
            'instagram': get_param('website_extra_social_media.instagram_link') or False,
            'whatsapp': get_param('website_extra_social_media.whatsapp_link') or False,
            'github': get_param('website_extra_social_media.github_link') or False,
            'youtube': get_param('website_extra_social_media.youtube_link') or False,
            'google_plus': get_param('website_extra_social_media.google_plus_link') or False,
            'snapchat': get_param('website_extra_social_media.snapchat_link') or False,
            'flickr': get_param('website_extra_social_media.flickr_link') or False,
            'quora': get_param('website_extra_social_media.quora_link') or False,
            'pinterest': get_param('website_extra_social_media.pinterest_link') or False,
            'dribbble': get_param('website_extra_social_media.dribbble_link') or False,
            'tumblr': get_param('website_extra_social_media.tumblr_link') or False,
        }
