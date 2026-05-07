# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models
from odoo.http import request


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_available_in_pos = fields.Boolean(string="Available In POS", default=False)

    def _clean_pos_values(self, vals):
        """ Fixes the 'integer = record' error by converting [id, name] to id """
        cleaned = {}
        for key, value in vals.items():
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], int):
                cleaned[key] = value[0]
            else:
                cleaned[key] = value
        return cleaned

    @api.model_create_multi
    def create(self, vals_list):
        # 1. DETECT IF CALL COMES FROM POS UI
        is_pos = False
        if request and hasattr(request, 'httprequest'):
            # Even if context is empty, the Referer URL tells us we are in POS
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
        """ Handles updates from the POS UI """
        is_pos = False
        if request and hasattr(request, 'httprequest'):
            if '/pos/ui' in (request.httprequest.referrer or ''):
                is_pos = True

        if is_pos:
            vals['is_available_in_pos'] = True

        cleaned = self._clean_pos_values(vals)
        return super().write(cleaned)

    @api.model
    def _load_pos_data_fields(self, config_id, *args, **kwargs):
        res = super()._load_pos_data_fields(config_id, *args, **kwargs)
        if 'is_available_in_pos' not in res:
            res.append('is_available_in_pos')
        return res

    @api.model
    def _load_pos_data_domain(self, data, *args, **kwargs):
        domain = super()._load_pos_data_domain(data, *args, **kwargs)
        domain.append(('is_available_in_pos', '=', True))
        return domain
