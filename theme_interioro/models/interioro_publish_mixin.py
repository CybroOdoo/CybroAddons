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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
"""
This module contains the InterioroPublishMixin abstract model.
It provides common fields and logic for models that need to be published
on the website, including slug generation and translation support.
"""
import re
from odoo import api, fields, models
from odoo.tools.translate import html_translate


class InterioroPublishMixin(models.AbstractModel):
    """
    Abstract model to provide common website publishing functionality.

    This mixin includes fields for naming, slugging, sequencing, imaging,
    and description (both short and full). It also handles automatic
    slug generation from the record name.
    """
    _name = 'interioro.publish.mixin'
    _description = 'Interioro Publish Mixin'
    _order = 'sequence, id'

    name = fields.Char('Name', help='Name', required=True, translate=True)
    slug = fields.Char('URL Slug', required=True, copy=False,
                               help='Auto-generated from name. Used in the page URL.')
    sequence = fields.Integer('Sequence', help='Sequence', default=10)
    image = fields.Image('Main Image', help='Image', max_width=1200, max_height=900)
    short_desc = fields.Char('Short Description', translate=True,
                               help='One-line summary shown on listing/carousel cards')
    description = fields.Html('Full Description', translate=html_translate,
                               sanitize=False,
                               help='Rich content shown on the detail page')
    is_published = fields.Boolean('Published on Website', help='Mark Published on Website or not', default=True)
    active = fields.Boolean(default=True)

    @staticmethod
    def _slugify(name):
        """
        Convert a string into a URL-friendly slug.

        :param str name: The string to slugify (usually the record name).
        :return str: A slugified version of the input string.
        """
        s = name.lower().strip()
        return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create to automatically generate a slug if not provided.

        :param list vals_list: List of values for record creation.
        :return recordset: The created records.
        """
        for v in vals_list:
            if not v.get('slug') and v.get('name'):
                v['slug'] = self._slugify(v['name'])
        return super().create(vals_list)

    def toggle_is_published(self):
        """
        Toggle published state — called from form stat button.
        """
        for rec in self:
            rec.is_published = not rec.is_published
