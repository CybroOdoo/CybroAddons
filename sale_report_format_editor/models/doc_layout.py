# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swathy K S (odoo@cybrosys.com)
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
##############################################################################
from odoo import fields, models


class DocLayout(models.Model):
    """Used for designing the document template of sale"""
    _name = "doc.layout"
    _description = 'Layout Customization'

    name = fields.Char(string="Name", help="Name of the Layout")
    base_color = fields.Char(string="Base Color",
                             help="Background color for the invoice")
    heading_text_color = fields.Char(string="Heading Text Color",
                                     help="Text color for headings")
    text_color = fields.Char(string="Text Color", help="Text color of items")
    customer_text_color = fields.Char(string="Customer Text Color",
                                      help="Customer address text color")
    company_text_color = fields.Char(string="Company Text Color",
                                     help="Company address Text color")
    logo_position = fields.Selection([('left', 'Left'),
                                      ('right', 'Right')],
                                     string="Logo Position",
                                     help="Company logo position")
    customer_position = fields.Selection([('left', 'Left'),
                                          ('right', 'Right')],
                                         string="Customer position",
                                         help="Customer address position")
    company_position = fields.Selection([('left', 'Left'),
                                         ('right', 'Right')],
                                        string="Company Address Position",
                                        help="Company address position")
    sales_person = fields.Boolean(string='Sales person', default=True,
                                  help="Display sale person of the sale")
    description = fields.Boolean(string='Description', default=True,
                                 help="Display product description")
    tax_value = fields.Boolean(string='Tax', help="Applied tax of order line")
    reference = fields.Boolean(string='Customer Reference',
                               help="Display customer reference of the sale")
    tagline_position = fields.Selection(
        selection=[('left', 'Left'), ('right', 'Right')],
        string="Tagline Position", default='right',
        help="Company Tagline position")
    source = fields.Boolean(string='Source',
                            help="Display source document of the sale")
    address = fields.Boolean(string='Address',
                             help="Display customer address")
    city = fields.Boolean(string='City',
                          help="Display city of customer address")
    country = fields.Boolean(string='Country',
                             help="Display country of customer address")
    company_id = fields.Many2one('res.company', string='Company',
                                 help="Current Company",
                                 default=lambda self: self.env.company)
    vat = fields.Boolean(string='VAT', default=True,
                         help='Customer vat id')
    watermark = fields.Boolean(string='Watermark', help="Watermark on report",
                               related='company_id.watermark',
                               readonly=False)
    watermark_show = fields.Selection(
        [('logo', 'Company Logo'), ('name', 'Company Name')],
        default='logo', string="Watermark Show", help="Watermark types",
        related='company_id.watermark_show', readonly=False)
