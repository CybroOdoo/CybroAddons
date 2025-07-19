# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev KP (odoo@cybrosys.com)
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
################################################################################
"""This module enables users to place online orders and
pick up their purchases from nearby stores. """
from odoo import api, models


class PosSession(models.Model):
    """inherit pos session for load models in pos"""
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """Loading models in pos session"""
        models = super()._load_pos_data_models(config_id)
        models += ['stock.picking', 'stock.move', 'sale.order.line']
        return models
