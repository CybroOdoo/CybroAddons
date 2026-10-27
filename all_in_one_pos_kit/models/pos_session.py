# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
from odoo import api, models


class PosSession(models.Model):
    """Inherit pos session to load the multi barcode and the product
    planning (meals planning) records in the POS"""
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config):
        """Add the models used by this module to the models that are loaded
        into the Point of Sale when a session is started.

        :param config: pos.config record of the opened POS
        :return: list of model names loaded in the POS
        """
        data = super()._load_pos_data_models(config)
        for model in ('multi.barcode.products', 'meals.planning'):
            if model not in data:
                data.append(model)
        return data
