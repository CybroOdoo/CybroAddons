# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, fields


class DocLayout(models.Model):
    """Doc layout model"""
    _name = "doc.layout"
    _description = 'Document Layout'

    name = fields.Char(help="The name of the document layout")
    base_color = fields.Char(help="Background color for the invoice")
    heading_text_color = fields.Char(help="Heading text color")
    text_color = fields.Char(help="Text color of items")
    customer_text_color = fields.Char(help="Customer address text color")
    company_text_color = fields.Char(help="Company address text color")
    logo_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        help="Company logo position")
    tagline_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        help="Company tagline position")
    customer_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        help="Customer address position")
    company_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Company Address Position",
        help="Company address position")
    sales_person = fields.Boolean(default=True,
                                  help="Sales Person of the layout")
    description = fields.Boolean(default=True,
                                 help="Description of the layout")
    tax_value = fields.Boolean(string='Tax', default=True,
                               help="Tax of the layout")
    reference = fields.Boolean(string='Customer Reference', default=True,
                               help="Customer Reference")
    source = fields.Boolean(default=False,
                            help="Source Document of the layout")
    address = fields.Boolean(default=True,
                             help="Address of the document layout")
    city = fields.Boolean(default=True,
                          help="City of the document layout")
    country = fields.Boolean(default=True,
                             help="Country of the document layout")
    vat = fields.Boolean(string='VAT', default=True,
                         help='Customer vat id')
