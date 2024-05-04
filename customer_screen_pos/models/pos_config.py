# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (odoo@cybrosys.com)
#
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
###############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Extend functionality of Point of Sale Configuration"""
    _inherit = 'pos.config'

    allow_customer_screen = fields.Boolean(string="Customer Screen",
                                           help='Allows the screen share with'
                                                'the customers')
    allow_systray_icon = fields.Boolean(string="Allow Systray Button",
                                        help='Allows the customer to set '
                                             'screen open button in systray')
    allow_product_click = fields.Boolean(string="Allow Product Click",
                                         help='Allows the customer to set '
                                              'screen open when click product')
