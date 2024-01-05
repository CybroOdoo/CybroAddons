# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Javid A(<https://www.cybrosys.com>)
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
        A class that inherits the existing transient model res.config.settings
    """
    _inherit = 'res.config.settings'

    website_order_configuration = fields.Selection(
        [('confirm_order', 'Confirm Quotation'),
         ('confirm_order_create_inv', 'Confirm Quotation and Create Invoice'),
         ('confirm_order_post_inv', 'Confirm Quotation and Validate Invoice'),
         ('confirm_quotation_create_payment',
          'Confirm Quotation, Validate Invoice and Create Payment')],
        string='Website Order Configuration',
        default='confirm_order',
        help="Option to choose the automatic workflow of website sale order",
        config_parameter='website_sale_auto_backend.website_order_configuration')
