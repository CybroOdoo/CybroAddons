# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Adding a new fields to res_config_settings model for filtering the
    low sales report"""
    _inherit = "res.config.settings"

    product_type = fields.Selection(
        [('variant', 'By product variant'),
         ('template', 'By product templates')], string="Report Type",
        help='Which sale to take into account: Product templates in general'
             ' or variants?',
        config_parameter='low_sale_report.product_type')
    analysed_period = fields.Selection(
        [('last_month', 'Last Month'),
         ('last_3', 'Last 3 Month'), ('last_6', 'Last 6 Month'),
         ('last_12', 'Last 12 Month')], string='Analysed Period',
        help='Define the which period should be analysed by default.',
        config_parameter='low_sale_report.analysed_period')
    absolute_qty = fields.Float(string='Absolute Quantity',
                                help='Define a default critical level for '
                                     'sales.',
                                config_parameter='low_sale_report.absolute_qty')
