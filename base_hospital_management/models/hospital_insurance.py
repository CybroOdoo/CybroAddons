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


class HospitalInsurance(models.Model):
    """Class holding insurance details"""
    _name = 'hospital.insurance'
    _description = 'Hospital Insurance'

    name = fields.Char(string='Provider', help='Name of the insurance provider')
    currency_id = fields.Many2one('res.currency',
                                  help='Currency in which insurance will be '
                                       'calculated',
                                  default=lambda self: self.env.company
                                  .currency_id.id,
                                  required=True)
    total_coverage = fields.Monetary(help='Total coverage of the insurance')
