# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies M  (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,

#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################.
from odoo import api, models

class PosSession(models.Model):
    _inherit = "pos.session"


    @api.model
    def _pos_ui_models_to_load(self):
        result = super()._pos_ui_models_to_load()
        new_model = 'loyalty.card'
        if new_model not in result:
            result.append(new_model)
        return result

    @api.model
    def _loader_params_loyalty_card(self):
        return {"search_params": {"domain": [], "fields": ["id","points","set_limit", "balance_limit_amount"]}}

    def _get_pos_ui_loyalty_card(self, params):
        return self.env['loyalty.card'].search_read(**params['search_params'])