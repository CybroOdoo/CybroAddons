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


class ResConfigSettings(models.TransientModel):
    """ Class for inherited model res config settings. Contains required
        fields and functions for the website_extra_social_media module.
        Methods:
            get_social_media_values(self):
                Method for return social media value into the website."""
    _inherit = 'res.config.settings'

    social_whatsapp = fields.Char(related='website_id.social_whatsapp',
                                  readonly=False)
    social_google_plus = fields.Char(related='website_id.social_google_plus',
                                     readonly=False)
    social_snapchat = fields.Char(related='website_id.social_snapchat',
                                  readonly=False)
    social_flickr = fields.Char(related='website_id.social_flickr',
                                readonly=False)
    social_quora = fields.Char(related='website_id.social_quora',
                               readonly=False)
    social_pinterest = fields.Char(related='website_id.social_pinterest',
                                   readonly=False)
    social_dribble = fields.Char(related='website_id.social_dribble',
                                 readonly=False)
    social_tumblr = fields.Char(related='website_id.social_tumblr',
                                readonly=False)
