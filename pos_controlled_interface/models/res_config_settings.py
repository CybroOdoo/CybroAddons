# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Bhagyadev K P(<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inheriting res_config_settings model to add fields control_discount and
     control_price"""
    _inherit = 'res.config.settings'

    control_discount = fields.Boolean(string='Control Discount',
                                      related="pos_config_id.control_discount",
                                      readonly=False,
                                      help="Enable to control the discount")
    control_price = fields.Boolean(string='Control Price',
                                   related="pos_config_id.control_price",
                                   readonly=False,
                                   help="Enable to control the price")
