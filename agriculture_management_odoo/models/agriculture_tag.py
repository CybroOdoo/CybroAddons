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
from random import randint


class AgricultureTag(models.Model):
    """ This model represents tags related to agriculture. Tags are used to
       categorize and label various agricultural elements, products.
       They facilitate the organization and grouping of agricultural information
       for easier searching and classification. """
    _name = "agriculture.tag"
    _description = "Agriculture Tags"

    def _get_default_color(self):
        """ The function selects colors for tags, likely based on some
        criteria or input, facilitating visual differentiation and
        categorization."""
        return randint(1, 11)

    name = fields.Char(string='Tag Name', required=True, translate=True,
                       help='Tags are helpful for easy identification. Please '
                            'create appropriate tags.')
    color = fields.Integer(string='Color', default=_get_default_color,
                           help='Color are helpful for Highlight tags . Please'
                                'choose different colors for differed tags')

    _sql_constraints = [
        # Partial constraint, complemented by unique tag and name.
        # useful to keep because it provides a proper error message when a
        # violation occurs
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
