# -*- coding: utf-8 -*-
###################################################################################
#    Activity Management
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Technologies (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from random import randint
from odoo import fields, models


class ActivityTag(models.Model):
    """Model to add tags to an activity"""
    _name = "activity.tag"
    _description = "Activity Tag"

    def _get_default_color(self):
        """:returns random intrger between 1 and 11"""
        return randint(1, 11)

    name = fields.Char(string='Tag Name',
                       help='Name of the activity tag.',
                       required=True,
                       translate=True)
    color = fields.Integer(string='Color',
                           help='Field that gives color to tag.',
                           default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"), ]
