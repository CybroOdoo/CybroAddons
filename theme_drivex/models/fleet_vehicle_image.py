# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
"""
This module defines the Fleet Vehicle Image model.
"""
from odoo import fields, models


class FleetVehicleImage(models.Model):
    """Vehicle Gallery Image."""
    _name = 'fleet.vehicle.image'
    _description = 'Vehicle Gallery Image'
    _order = 'sequence, id'

    name = fields.Char(string="Name", help='Name of the image.')
    sequence = fields.Integer(string="Sequence", default=10,
                              help='Display sequence.')
    image = fields.Image(string="Image", required=True, max_width=1920,
                         max_height=1920, help='The image file.')
    vehicle_id = fields.Many2one(
        'fleet.vehicle', string="Vehicle", required=True,
        ondelete='cascade', help='Vehicle associated with the image.')
