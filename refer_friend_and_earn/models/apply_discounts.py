# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathti V (odoo@cybrosys.com)
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


class ApplyDiscounts(models.Model):
    """This class is used to define the discounts in percentage according the
    points acquired"""
    _name = 'apply.discounts'
    _description = 'Apply discounts according to the points'

    starting_points = fields.Integer(string='Starting point', help='Starting '
                                                                   'points')
    end_points = fields.Integer(string='Ending points', help='Ending points')
    discount = fields.Float(string='Discount in %', help='Discounts in '
                                                         'Percentage')
