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
"""Business Experience model"""
from odoo import fields, models


class BusinessExperience(models.Model):
    """Business experience inverse model."""
    _name = 'business.experience'
    _description = 'Business Experience'

    experience_name = fields.Char(string='Experience',
                                  help='Business Experience', required=True)
    from_date = fields.Date(help='Experience start Date')
    to_date = fields.Date(help='Experience To Date')
    experience_id = fields.Many2one('franchise.dealer',
                                    string='Franchise Dealer',
                                    help='Inverse field for Business'
                                         ' Experience model')
