# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Extend res.config.settings to store default configuration for low sales reporting."""

    _inherit = 'res.config.settings'

    product_type = fields.Selection(
        [('variant', 'By product variant'),
         ('template', 'By product templates')],
        string="Report Type",
        help="Which sale to take into account: Product templates in general"
             " or variants?",
        config_parameter='low_sale_report.product_type',
    )
    analysed_period = fields.Selection(
        [('last_month', 'Last Month'),
         ('last_3', 'Last 3 Months'),
         ('last_6', 'Last 6 Months'),
         ('last_12', 'Last 12 Months')],
        help="Define which period should be analysed by default.",
        config_parameter='low_sale_report.analysed_period',
    )
    absolute_qty = fields.Float(
        string="Absolute Quantity",
        help="Define a default critical level for sales.",
        config_parameter='low_sale_report.absolute_qty',
    )
