# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Bhagyadev KP (<https://www.cybrosys.com>)
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
################################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Used to add new fields to the settings"""
    _inherit = "pos.config"

    customer_details = fields.Boolean(string=" Customer Details",
                                      help="By Enabling the customer details"
                                           " in pos receipt")
    customer_name = fields.Boolean(string=" Customer Name",
                                   help="By Enabling the customer name "
                                        "in pos receipt")
    customer_address = fields.Boolean(string=" Customer Address",
                                      help="By Enabling the customer Address "
                                           "in pos receipt")
    customer_mobile = fields.Boolean(string=" Customer Mobile",
                                     help="By Enabling the customer mobile "
                                          "in pos receipt")
    customer_phone = fields.Boolean(string=" Customer Phone",
                                    help="By Enabling the customer phone "
                                         "in pos receipt")
    customer_email = fields.Boolean(string=" Customer Email",
                                    help="By Enabling the customer email "
                                         "in pos receipt")
    customer_vat = fields.Boolean(string=" Customer Vat",
                                  help="By Enabling the customer vat details "
                                       "in pos receipt")
