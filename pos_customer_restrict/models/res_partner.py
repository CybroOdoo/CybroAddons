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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import api, fields, models
from odoo.http import request


class ResPartner(models.Model):
    """Inherit res.partner to restrict customer visibility in Point of Sale."""

    _inherit = 'res.partner'

    is_available_in_pos = fields.Boolean(string="Available In POS", default=False)

    def _clean_pos_values(self, vals):
        """Convert relational [id, name] pairs to integer id for POS compatibility."""
        cleaned = {}
        for key, value in vals.items():
            field = self._fields.get(key)
            if field and field.type != 'many2one':
                cleaned[key] = value
            elif (
                isinstance(value, (list, tuple))
                and len(value) == 2
                and isinstance(value[0], int)
                and isinstance(value[1], str)
            ):
                cleaned[key] = value[0]
            else:
                cleaned[key] = value
        return cleaned

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle POS partner creation and clean relational values."""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]

        is_pos = False
        if request and hasattr(request, 'httprequest'):
            referer = request.httprequest.referrer or ''
            if '/pos/ui' in referer:
                is_pos = True

        for vals in vals_list:
            if is_pos:
                vals['is_available_in_pos'] = True

            cleaned = self._clean_pos_values(vals)
            vals.update(cleaned)

        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle POS partner updates and clean relational values."""
        is_pos = False
        if request and hasattr(request, 'httprequest'):
            referer = request.httprequest.referrer or ''
            if '/pos/ui' in referer:
                is_pos = True

        if is_pos:
            vals['is_available_in_pos'] = True

        cleaned = self._clean_pos_values(vals)
        return super().write(cleaned)

    @api.model
    def _load_pos_data_fields(self, config, *args, **kwargs):
        """Include is_available_in_pos in the fields loaded into the POS session."""
        res = super()._load_pos_data_fields(config, *args, **kwargs)
        if 'is_available_in_pos' not in res:
            res.append('is_available_in_pos')
        return res

    @api.model
    def _load_pos_data_domain(self, data, *args, **kwargs):
        """Filter partners to only load those available in POS."""
        domain = super()._load_pos_data_domain(data, *args, **kwargs)
        domain.append(('is_available_in_pos', '=', True))
        return domain
