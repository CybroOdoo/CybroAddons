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
import re
from odoo import api, fields, models
from odoo.tools.translate import html_translate


class InterioroPublishMixin(models.AbstractModel):
    """Shared fields and slug logic for Interioro catalogue models."""
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
        s = name.lower().strip()
        return re.sub(r'[^a-z0-9]+', '-', s).strip('-')

    @api.model_create_multi
    def create(self, vals_list):
        for v in vals_list:
            if not v.get('slug') and v.get('name'):
                v['slug'] = self._slugify(v['name'])
        return super().create(vals_list)

    def toggle_is_published(self):
        """Toggle published state — called from form stat button."""
        for rec in self:
            rec.is_published = not rec.is_published
