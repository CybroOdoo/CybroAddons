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


class CropAnimal(models.Model):
    """ This model serves as a bridge to attach animal details to crop
    request records. It provides a structured way to associate animal-related
    information with specific crop requests."""
    _name = 'crop.animal'
    _description = 'Crop Animal Details'

    dec_id = fields.Many2one('crop.request', string='Crop',
                             help='Select the crop id for this animal to be '
                                  'used')
    animal_id = fields.Many2one('animal.detail', string='Animal',
                                help="select animal used for this farming",
                                domain=[('state', '=', 'available')],
                                tracking=True)
    qty = fields.Integer(string='Quantity',
                         help=" Number of animals used for farming")
    company_id = fields.Many2one(
        'res.company', string='Company', required=True,
        readonly=True, help='This field represents the company associated with '
        'the current user or environment.', default=lambda self: self.env.company)
