# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (odoo@cybrosys.com)
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
from odoo import fields, models


class HotelAmenity(models.Model):
    """Model that handles all amenities of the hotel"""
    _name = 'hotel.amenity'
    _description = "Hotel Amenity"
    _inherit = 'mail.thread'
    _order = 'id desc'

    name = fields.Char(string='Name', help="Name of the amenity")
    icon = fields.Image(string="Icon", required=True,
                        help="Image of the amenity")
    description = fields.Html(string="About",
                              help="Specify the amenity description")
