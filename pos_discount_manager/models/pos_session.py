# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:Anjhana A K(<https://www.cybrosys.com>)
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
    """Inherited model POS Session for loading field in hr.employee into
       pos session.
       
       Methods:
           _pos_ui_models_to_load(self):
              to load model hr employee to pos session.
              
           _loader_params_hr_employee(self):
              loads field limited_discount to pos session.

       """
    _inherit = "pos.session"

    def _pos_ui_models_to_load(self):
        """Load hr.employee model into pos session"""
        result = super()._pos_ui_models_to_load()
        result += ['hr.employee']
        return result

    def _loader_params_hr_employee(self):
        """load hr.employee parameters"""
        result = super()._loader_params_hr_employee()
        result['search_params']['fields'].extend(
            ['limited_discount'])
        return result
