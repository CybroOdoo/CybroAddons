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
from odoo import fields, models


class FlynovaTravellerPhoto(models.Model):
    """Store traveller photos displayed by the Flynova website snippets."""

    _name = 'flynova.traveller.photo'
    _description = 'Flynova Traveller Photo'
    _order = 'sequence, id'

    name = fields.Char(
        string='Traveller Name', required=True,
        help='Traveller name shown as a caption beneath the photo on the website.')
    image_1920 = fields.Image(
        string='Photo', required=True, max_width=1920, max_height=1920,
        help='Traveller photo displayed in the gallery/testimonial snippet on the website.')
    image_128 = fields.Image(
        string='Photo (128)', related='image_1920', max_width=128,
        max_height=128, store=True, readonly=True,
        help='Auto-generated 128px thumbnail used in compact views. Read-only.')
    sequence = fields.Integer(
        string='Display Order', default=10,
        help='Display order in the website carousel; lower numbers appear first.')
    active = fields.Boolean(
        string='Active', default=True,
        help='Uncheck to hide this photo from the website without deleting it.')
