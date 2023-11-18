# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Amaya Aravind(odoo@cybrosys.com)
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
    """ Class for inherited model res config settings. Contains required
        fields and functions for the website_extra_social_media module.
        Methods:
            get_social_media_values(self):
                Method for return social media value into the website."""
    _inherit = 'res.config.settings'

    twitter_link = fields.Char(string='Twitter',
                               config_parameter='website_extra_social_media.twitter_link',
                               help='Add your Twitter account link')
    linkedin_link = fields.Char(string='LinkedIn',
                                config_parameter='website_extra_social_media.linkedin_link',
                                help='Add your LinkedIn account link')
    whatsapp_link = fields.Char(string='Whatsapp Number',
                                config_parameter='website_extra_social_media.whatsapp_link',
                                help='Add your Whatsapp Number')
    instagram_link = fields.Char(string='Instagram',
                                 config_parameter='website_extra_social_media.instagram_link',
                                 help='Add your Instagram account link')
    github_link = fields.Char(string='GitHub',
                              config_parameter='website_extra_social_media.github_link',
                              help='Add your GitHub account link')
    youtube_link = fields.Char(string='YouTube',
                               config_parameter='website_extra_social_media.youtube_link',
                               help='Add your YouTube account link')
    google_plus_link = fields.Char(string='Google Plus',
                                   config_parameter='website_extra_social_media.google_plus_link',
                                   help='Add your Google Plus account link')
    snapchat_link = fields.Char(string='Snapchat',
                                config_parameter='website_extra_social_media.snapchat_link',
                                help='Add your Snapchat account link')
    facebook_link = fields.Char(string='Facebook',
                                config_parameter='website_extra_social_media.facebook_link',
                                help='Add your Facebook account link')
    flickr_link = fields.Char(string='Flickr',
                              config_parameter='website_extra_social_media.flickr_link',
                              help='Add your Flickr account link')
    quora_link = fields.Char(string='Quora',
                             config_parameter='website_extra_social_media.quora_link',
                             help='Add your Quora account link')
    pinterest_link = fields.Char(string='Pinterest',
                                 config_parameter='website_extra_social_media.pinterest_link',
                                 help='Add your Pinterest account link')
    dribble_link = fields.Char(string='Dribble',
                               config_parameter='website_extra_social_media.dribble_link',
                               help='Add your Dribble account link')
    tumblr_link = fields.Char(string='Tumblr',
                              config_parameter='website_extra_social_media.tumblr_link',
                              help='Add your Tumblr account link')

    def get_social_media_values(self):
        """ Method for return social media value into the website."""
        return {
            'facebook': self.sudo().default_get(list(self.fields_get()))[
                'facebook_link'],
            'twitter': self.sudo().default_get(list(self.fields_get()))[
                'twitter_link'],
            'linkedin': self.sudo().default_get(list(self.fields_get()))[
                'linkedin_link'],
            'instagram': self.sudo().default_get(list(self.fields_get()))[
                'instagram_link'],
            'whatsapp': self.sudo().default_get(list(self.fields_get()))[
                'whatsapp_link'],
            'github': self.sudo().default_get(list(self.fields_get()))[
                'github_link'],
            'youtube': self.sudo().default_get(list(self.fields_get()))[
                'youtube_link'],
            'google_plus': self.sudo().default_get(list(self.fields_get()))[
                'google_plus_link'],
            'snapchat': self.sudo().default_get(list(self.fields_get()))[
                'snapchat_link'],
            'flickr': self.sudo().default_get(list(self.fields_get()))[
                'flickr_link'],
            'quora': self.sudo().default_get(list(self.fields_get()))[
                'quora_link'],
            'pinterest': self.sudo().default_get(list(self.fields_get()))[
                'pinterest_link'],
            'dribble': self.sudo().default_get(list(self.fields_get()))[
                'dribble_link'],
            'tumblr': self.sudo().default_get(list(self.fields_get()))[
                'tumblr_link'],
        }
