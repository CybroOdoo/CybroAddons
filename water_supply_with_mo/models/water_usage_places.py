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
#############################################################################
from odoo import fields, models


class WaterUsagePlaces(models.Model):
    """Creating water usage places."""
    _name = 'water.usage.places'
    _description = 'Water Usage Places'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'usage_place_name'

    code = fields.Char(string='Code', help='Code of the water usage place', required=True)
    usage_place_name = fields.Char(string='Usage Place Name',
                                   help='Name of the water usage place', required=True)
