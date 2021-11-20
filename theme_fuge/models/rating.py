# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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


class Rating(models.Model):
    _inherit = 'product.template'

    def _count_rating_count(self):
        for rec in self:
            reviews = rec.rating_get_stats()
            count_avg = reviews.get('avg')
            rec.rating_count = count_avg

    def _count_rating_total(self):
        for rec in self:
            reviews = rec.rating_get_stats()
            count_total = reviews.get('total')
            rec.rating_total = count_total

    rating_count = fields.Float(compute='_count_rating_count', string='Average Rating')
    rating_total = fields.Integer(compute='_count_rating_total', string='Total Rating')

