# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, fields


class LocationDetails(models.Model):
    _name = 'location.details'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Location Details"
    _rec_name = 'location_name'

    location_name = fields.Char(string='Location Name', required=True,
                                tracking=True)
    location_address = fields.Char(string='Location Address', required=True,
                                   tracking=True)
    location_area = fields.Float(string='Location Area', required=True,
                                 tracking=True)
    location_area_unit = fields.Selection(
        [('acres', 'Acres'), ('hectares', 'Hectares')], string='Area Unit',
        required=True, tracking=True)
    location_type = fields.Selection([('plot', 'Plot'), ('field', 'Field')],
                                     default="plot",
                                     string='Location Type', required=True,
                                     tracking=True)
    note = fields.Text(string='Note', tracking=True)
