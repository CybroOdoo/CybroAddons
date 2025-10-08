# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Abhin K(odoo@cybrosys.com)
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


class DocLayoutPurchase(models.Model):
    """Model is created to add customizations to the pdf report"""

    _name = "doc.layout.purchase"
    _description = "Doc Layout Purchase"

    name = fields.Char(string="Name", help="Name of the record")
    base_color = fields.Char(string="Base Color",
                             help="Background color for the invoice")
    heading_text_color = fields.Char(string="Heading text Color",
                                     help="Heading Text color")
    text_color = fields.Char(string="Text Color", help="Text color of items")
    customer_text_color = fields.Char(string="Customer Text Color",
                                      help="Customer address text color")
    company_text_color = fields.Char(string="Company Text Color",
                                     help="Company address Text color")
    logo_position = fields.Selection(selection=[("left", "Left"),
                                                ("right", "Right")],
                                     string="Logo Position",
                                     help="Company logo position")
    customer_position = fields.Selection(selection=[("left", "Left"),
                                                    ("right", "Right")],
                                         string="Customer position",
                                         help="Customer address position")
    shipping_address = fields.Boolean(string="Shipping Address",
                                      default=True,
                                      help="Enable shipping address if "
                                           "required to print on report.")
    shipping_address_position = fields.Selection(
        selection=[("left", "Left"), ("right", "Right")],
        string="Shipping Address position",
        help="Select the Customer address position")
    company_position = fields.Selection(
        selection=[("left", "Left"), ("right", "Right")],
        string="Company Address Position",
        help="The position of the company address")
    purchase_rep = fields.Boolean(string="Purchase Representative",
                                  default=False,
                                  help="Indicates whether the contact is a "
                                       "Purchase Representative.")
    description = fields.Boolean(string="Description", default=False,
                                 help=" Indicates whether a description "
                                      "is included.")
    code = fields.Boolean(string="Internal Reference", default=False,
                          help="Indicates whether an internal reference "
                               "(HSN code) is included.")
    tax_value = fields.Boolean(string="Tax", default=False,
                               help="Indicates whether the tax value is "
                                    "included.")
    reference = fields.Boolean(string="Order Reference", default=False,
                               help="Indicates whether the customer reference "
                                    "(order reference) is included.")
    source = fields.Boolean(string="Source", default=False,
                            help="Indicates whether the source document is "
                                 "included.")
    address = fields.Boolean(string="Address", default=False,
                             help="Indicates whether the address is included.")
    city = fields.Boolean(string="City", default=False,
                          help="Indicates whether the city is included.")
    country = fields.Boolean(string="Country", default=False,
                             help="Indicates whether the Country is included.")
