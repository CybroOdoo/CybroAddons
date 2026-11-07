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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ApplyDiscounts(models.Model):
    """To manage discounts based on the points"""
    _name = 'apply.discounts'
    _description = 'Apply Discounts According to Points'

    starting_points = fields.Integer(string='Starting Points')
    end_points = fields.Integer(string='Ending Points')
    discount = fields.Float(string='Discount in %', help='Discounts in Percentage')

    @api.constrains('starting_points', 'end_points')
    def _check_points_range(self):
        """Check if points range is valid"""
        for rec in self:
            if rec.starting_points > rec.end_points:
                raise ValidationError(
                    "Starting points must be less than or equal to ending points."
                )
