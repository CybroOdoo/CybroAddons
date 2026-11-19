# -*- coding: utf-8 -*-
#################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################

from odoo import api, fields, models


class HrEmployeePublic(models.Model):
    """Add field into hr employee"""
    _inherit = 'hr.employee.public'

    limited_discount = fields.Float(string="Discount Limit (%)",
                                    digits='Discount',
                                    help="Provide discount limit to each "
                                         "employee",
                                    related="employee_id.limited_discount")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Loading fields"""
        result = super()._load_pos_data_fields(config_id)
        result.append('limited_discount')
        return result
