# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields,models


class FlynovaTravellerPhoto(models.Model):
    """Flynova Traveller Photo"""
    _name = 'flynova.traveller.photo'
    _description = 'Flynova Traveller Photo'
    _order = 'sequence, id'

    name = fields.Char(string="Name", required=True,
                       help="Full name of the traveller whose photo is being featured on the website.")
    image_1920 = fields.Image(string='Photo', required=True, max_width=1920, max_height=1920,
                              help="High-resolution traveller photo displayed in the website gallery. Maximum size: 1920×1920 px.")
    sequence = fields.Integer(string="Sequence", default=10,
                              help="Controls the display order of photos in the gallery. Lower values appear first.")
    active = fields.Boolean(string="Active", default=True,
                            help="Uncheck to hide this photo from the website gallery without deleting it.")
