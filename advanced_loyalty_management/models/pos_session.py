# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models


class PosSession(models.Model):
    """to load more fields in loyalty program and loyalty model"""
    _inherit = 'pos.session'

    def _loader_params_loyalty_program(self):
        """To load more fields in the model loyalty.program"""
        result = super()._loader_params_loyalty_program()
        result['search_params']['fields'].extend(['point_rate', 'change_rate'])
        return result

    def _loader_params_loyalty_reward(self):
        """to load more fields in the model loyalty.reward"""
        result = super()._loader_params_loyalty_reward()
        result['search_params']['fields'].extend(
            ['redemption_point', 'redemption_amount', 'max_redemption_amount',
              'redemption_frequency',
             'redemption_frequency_unit', 'redemption_eligibility',
             'max_redemption_type'])
        return result

    def _loader_params_res_partner(self):
        result = super()._loader_params_res_partner()
        result['search_params']['fields'].extend(['pos_order_ids'])
        return result
