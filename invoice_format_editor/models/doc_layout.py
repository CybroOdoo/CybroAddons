# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ajith V(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import models, fields


class AddDocumentTemplate(models.Model):
    """Doc layout model"""
    _name = "doc.layout"
    _description = 'Adding the fields for customization'
    _rec_name = 'name'

    name = fields.Char(string="Name", help="The name of the document layout")
    base_color = fields.Char(string="Base Color",
                             help="Background color for the invoice")
    heading_text_color = fields.Char(string="Heading text Color",
                                     help="Heading Text color")
    text_color = fields.Char(string="Text Color",
                             help="Text color of items")
    customer_text_color = fields.Char(string="Customer Text Color",
                                      help="Customer address text color")
    company_text_color = fields.Char(string="Company Text Color",
                                     help="Company address Text color")
    logo_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Logo Position",
        help="Company logo position")
    tagline_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Tagline Position",
        help="Company Tagline position")
    customer_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Customer position",
        help="Customer address position")
    company_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Company Address Position",
        help="Company address position")
    sales_person = fields.Boolean(string='Sales person', default=True,
                                  help="Sales Person of the layout")
    description = fields.Boolean(string='Description', default=True,
                                 help="Description of the layout")
    tax_value = fields.Boolean(string='Tax', default=True,
                               help="Tax of the layout")
    reference = fields.Boolean(string='Customer Reference', default=True,
                               help="Customer Reference")
    source = fields.Boolean(string='Source', default=False,
                            help="Source Document of the layout")
    address = fields.Boolean(string='Address', default=True,
                             help="Address of the document layout")
    city = fields.Boolean(string='City', default=True,
                          help="City of the document layout")
    country = fields.Boolean(string='Country', default=True,
                             help="Country of the document layout")
    vat = fields.Boolean(string='VAT', default=True,
                         help='Customer vat id')
