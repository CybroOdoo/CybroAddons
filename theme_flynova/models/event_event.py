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


class EventEvent(models.Model):
    """Event Event"""
    _inherit = 'event.event'

    image_1920 = fields.Image(string="Event Image", max_width=1920, max_height=1920,
                              help="Main image displayed for this event on the Flynova website.")
    image_128 = fields.Image(string="Event Image (128)", related='image_1920',
                             max_width=128, max_height=128, store=True, readonly=True,
                             help="Auto-generated thumbnail (128×128) derived from the main event image.")
    duration = fields.Char(string="Duration", help="e.g. 1 Week, 5 Days")
    location_name = fields.Char(string="Location", help="e.g. Thailand, Japan")
