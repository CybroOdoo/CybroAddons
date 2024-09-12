# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM(odoo@cybrosys.com)
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


class Website(models.Model):
    """Inheritance model for website models that adding new methods"""
    _inherit = "website"

    def _default_social_whatsapp(self):
        return self.env.ref('base.main_company').social_whatsapp

    def _default_social_google_plus(self):
        return self.env.ref('base.main_company').social_google_plus

    def _default_social_snapchat(self):
        return self.env.ref('base.main_company').social_snapchat

    def _default_social_social_flickr(self):
        return self.env.ref('base.main_company').social_flickr

    def _default_social_social_quora(self):
        return self.env.ref('base.main_company').social_quora

    def _default_social_social_pinterest(self):
        return self.env.ref('base.main_company').social_pinterest

    def _default_social_dribble(self):
        return self.env.ref('base.main_company').social_dribble

    def _default_social_tumblr(self):
        return self.env.ref('base.main_company').social_tumblr

    social_whatsapp = fields.Char('Whatsapp Number',
                                  default=_default_social_whatsapp)
    social_google_plus = fields.Char('Google+ Account',
                                     default=_default_social_google_plus)
    social_snapchat = fields.Char('SnapChat Account',
                                  default=_default_social_snapchat)
    social_flickr = fields.Char('Flickr Account',
                                default=_default_social_social_flickr)
    social_quora = fields.Char('Quora Account',
                               default=_default_social_social_quora)
    social_pinterest = fields.Char('Pinterest Account',
                                   default=_default_social_social_pinterest)
    social_dribble = fields.Char('Dribble Account',
                                 default=_default_social_dribble)
    social_tumblr = fields.Char('Tumblr Account',
                                default=_default_social_tumblr)
