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
from odoo import api, fields, models


class HrEmployee(models.Model):
    """Add field into hr employee"""
    _inherit = 'hr.employee'

    limited_discount = fields.Integer(string="Discount Limit",
                                      help="Provide discount limit to each "
                                           "employee")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Loading fields"""
        result = super()._load_pos_data_fields(config_id)
        result.append('limited_discount')
        result.append('parent_id')
        result.append('pin')
        return result
