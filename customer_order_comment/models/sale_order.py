# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
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
""" This module inherits sale.order to add new fields. """
from odoo import fields, models


class SaleOrder(models.Model):
    """ Inherits sale.order to add the fields comment and rating """
    _inherit = 'sale.order'

    comment = fields.Char(string='Comment', readonly=True,
                          help='The comment provided by the customer.')
    rating = fields.Selection([
        ('1', 'Poor'), ('2', 'Too Bad'), ('3', 'Average Quality'),
        ('4', 'Nice'), ('5', 'Good')], string='Rating', readonly=True,
        help='The rating provided by the customer.')
