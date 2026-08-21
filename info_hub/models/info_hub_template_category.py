# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import fields, models

class InformationTemplateCategory(models.Model):
    """Groups info article templates for easier browsing in the template picker.

    Categories are displayed in the 'Browse Templates' dialog with an optional emoji
    icon and a configurable sort sequence.
    """

    _name = 'info.hub.template.category'
    _description = 'Information Template Category'
    _order = 'sequence, name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help='Name of the template category.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for displaying template categories.',
    )
    icon = fields.Char(
        string='Emoji Icon',
        size=5,
        default='📁',
        help='A single emoji character to visually represent this category.',
    )

    _name_uniq = models.Constraint('UNIQUE (name)', 'A category with this name already exists!')
