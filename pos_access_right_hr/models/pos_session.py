# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Viswanth k (odoo@cybrosys.com)
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
    """
    The inherited class PosSession to add new fields and models to pos.session
    """
    _inherit = 'pos.session'

    def _loader_params_hr_employee(self):
        """
        Method for loading hr_employee fields to pos.session
        :return: dictionary containing hr_employee access right fields
        """
        result = super()._loader_params_hr_employee()
        result['search_params']['fields'].extend(
            ['disable_payment', 'disable_customer', 'disable_plus_minus',
             'disable_numpad', 'disable_qty', 'disable_discount',
             'disable_price', 'disable_remove_button'])
        return result
