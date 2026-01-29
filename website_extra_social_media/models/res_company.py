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


class Company(models.Model):
    """Inherits the Company model for adding new fields"""
    _inherit = "res.company"

    social_whatsapp = fields.Char(string='Whatsapp Number')
    social_google_plus = fields.Char(string='Google+ Account')
    social_snapchat = fields.Char(string='SnapChat Account')
    social_flickr = fields.Char(string='Flickr Account')
    social_quora = fields.Char(string='Quora Account')
    social_pinterest = fields.Char(string='Pinterest Account')
    social_dribble = fields.Char(string='Dribble Account')
    social_tumblr = fields.Char(string='Tumblr Account')
