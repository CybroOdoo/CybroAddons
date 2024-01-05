# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models


class PosSession(models.Model):
    """
    Inheriting pos_session module to load fields in pos session
    """
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        """Function to load product_discount_limit in pos session"""
        result = super()._loader_params_product_product()
        result['search_params']['fields'].extend(
            ['product_discount_limit'])
        return result

    def _loader_params_pos_category(self):
        """Function to load discount_limit in pos session"""
        result = super()._loader_params_pos_category()
        result['search_params']['fields'].extend(
            ['discount_limit'])
        return result

    def _loader_params_hr_employee(self):
        """Function to load has_pos_discount_control in pos"""
        result = super()._loader_params_hr_employee()
        result['search_params']['fields'].extend(['has_pos_discount_control'])
        return result
