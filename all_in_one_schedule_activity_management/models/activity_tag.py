# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models
from random import randint


class ActivityTag(models.Model):
    """This class is used to create tags for activity"""
    _name = "activity.tag"
    _description = "Activity Tag"

    def _get_default_color(self):
        """Return random number"""
        return randint(1, 11)

    name = fields.Char('Tag Name', required=True, translate=True,
                       help="Tag name")
    color = fields.Integer('Color', default=_get_default_color,
                           help="Tag color")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]
