# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sadique Kottekkat (<https://www.cybrosys.com>)
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
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """
    This is an Odoo model for configuration settings. It inherits from the
    'res.config.settings' model and extends its functionality by adding
    fields for low stock alert configuration
    """
    _inherit = 'res.config.settings'

    is_low_stock_alert = fields.Boolean(
        string="Low Stock Alert",
        help='This field determines the minimum stock quantity at which a low '
             'stock alert will be triggered.When the product quantity falls '
             'below this value, the background color for the product will be '
             'changed based on the alert state.',
        config_parameter='low_stocks_product_alert.is_low_stock_alert')
    min_low_stock_alert = fields.Integer(
        string='Alert Quantity', default=0,
        help='Change the background color for the product based'
             'on the Alert Quant.',
        config_parameter='low_stocks_product_alert.min_low_stock_alert')
