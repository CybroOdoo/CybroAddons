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
""" This module inherits sale.order to add new fields. """
from odoo import fields, models


class SaleOrder(models.Model):
    """ Inherits sale.order to add the fields comment and rating """
    _inherit = 'sale.order'

    comment = fields.Char(string='Comment', readonly=True,
                          help='The comment provided by the customer.')
    rating = fields.Selection([
        ('0', 'Not Rated'),
        ('1', 'Very Bad'),
        ('2', 'Poor'),
        ('3', 'Average Quality'),
        ('4', 'Good'),
        ('5', 'Very Good Quality'),
    ], string='Rating', readonly=True, default='0',
       help='The rating provided by the customer.')
