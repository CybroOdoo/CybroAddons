# -*- coding: utf-8 -*-
###############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Mohamed Muzammil VP(<https://www.cybrosys.com>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Lesser General Public License(LGPLv3) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from odoo import fields, models


class StockPicking(models.Model):
    """Adding some fields to stock.picking to print a report"""
    _inherit = 'stock.picking'

    enable_order_line = fields.Boolean(string='Include Product Details',
                                       default=True,
                                       help="If you want to print the product "
                                            "details in your report enable "
                                            "this field")
    vehicle_no = fields.Char(string='Vehicle Number',
                             help="Enter the vehicle number")
    vehicle_driver_name = fields.Char(string='Driver Name',
                                      help="Enter the driver's name")
    driver_contact_number = fields.Char(string='Contact No',
                                        help="Enter the driver's contact"
                                             " number")
    corresponding_company = fields.Char(string='Company',
                                        help="Enter the corresponding company")
