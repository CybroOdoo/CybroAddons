# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
################################################################################cybrosys:8018
from odoo import fields, models


class ConfigSettings(models.TransientModel):
    """Class for adding the fields in res.config.settings"""
    _inherit = 'res.config.settings'

    total_items = fields.Boolean(
        string="Enable Total Items", related="pos_config_id.pos_total_items",
        help="Enable this option will show the total number of items and "
             "total quantities of product in the PoS screen.", readonly=False)
    total_quantity = fields.Boolean(
        string="Enable Total Quantity", related="pos_config_id.pos_total_quantity",
        help="Enable this option will show the total number of items and total "
             "quantities of product in the receipt.", readonly=False)
