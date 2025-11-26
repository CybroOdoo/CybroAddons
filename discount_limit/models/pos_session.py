# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import api, models


class PosSession(models.Model):
    """
    Inheriting pos_session module to load fields in pos session
    """
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        """load the data to the pos.config.models"""
        data = super()._load_pos_data_models(config_id)
        data += ['hr.employee', 'product.product']
        return data

    def _loader_params_hr_employee(self):
        """Load the field birthdate to pos.session"""
        result = super()._loader_params_hr_employee()
        result['search_params']['fields'].append('has_pos_discount_control')
        return result
