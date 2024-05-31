# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vyshnav AR(<https://www.cybrosys.com>)
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
from odoo import fields, models


class CropMachinery(models.Model):
    """ This model serves as a bridge to attach machinery details to crop
    request records. It provides a structured way to associate machinery-related
    information with specific crop requests."""
    _name = 'crop.machinery'
    _description = 'Crop Machinery Details'

    des_id = fields.Many2one('crop.request', string='Crop id',
                             help="The crop id should be used to identify the "
                                  "machinery is used which crop farming")
    vehicle_id = fields.Many2one('vehicle.detail',
                                 help="The vehicle that used for farming",
                                 tracking=True, string='Vehicle',)
    qty = fields.Integer(string='Quantity',
                         help="The Number of the vehicle that used for farming")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='This field represents the company associated with'
        ' the current user or environment.', default=lambda self: self.env.company)
