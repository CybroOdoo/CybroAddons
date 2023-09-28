# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Fathima Mazlin AM (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE (LGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models


class PosSession(models.Model):
    """ Inherit pos session for load fields from res partner model"""
    _inherit = 'pos.session'

    def _pos_ui_models_to_load(self):
        """For load module to POS"""
        result = super()._pos_ui_models_to_load()
        result += [
            'res.partner.category',
        ]
        return result

    def _loader_params_res_partner_category(self):
        """For load res partner category fields"""
        return {
            'search_params': {'fields': ['name', 'partner_ids']}}

    def _get_pos_ui_res_partner_category(self, params):
        """For getting parameters of res partner category model"""
        return self.env['res.partner.category'].search_read(
            **params['search_params'])
