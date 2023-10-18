# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Arwa V V (Contact : odoo@cybrosys.com)
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
#############################################################################
from odoo import models


class PosSession(models.Model):
    """Inherits model 'pos.session' and loads fields and models"""
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Loading field 'pos_multi_uom_ids' to POS"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].append('pos_multi_uom_ids')
        return result

    def _pos_ui_models_to_load(self):
        """Loading model 'pos.multi.uom' to POS"""
        result = super()._pos_ui_models_to_load()
        result.append('pos.multi.uom')
        return result

    def _loader_params_pos_multi_uom(self):
        """Loading fields of model 'pos.multi.uom' to POS"""
        return {
            'search_params': {
                'fields': ['uom_id', 'price', 'product_template_id']}
        }

    def _get_pos_ui_pos_multi_uom(self, params):
        """Loading new model to POS"""
        return self.env['pos.multi.uom'].search_read(**params['search_params'])
