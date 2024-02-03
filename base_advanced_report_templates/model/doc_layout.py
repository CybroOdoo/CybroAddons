# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Ammu Raj (odoo@cybrosys.com)
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
################################################################################
from odoo import models, fields


class DocLayout(models.Model):
    """Adding the fields for customization"""
    _name = "doc.layout"
    _description = 'Adding the fields for customization'
    _rec_name = 'name'

    name = fields.Char(string="Name", help="Name of the layout")
    base_color = fields.Char(string="Base Color",
                             help="Background color for the invoice")
    heading_text_color = fields.Char(string="Heading text Color",
                                     help="Text color of the Heading")
    text_color = fields.Char(string="Text Color", help="Text color of items")
    customer_text_color = fields.Char(string="Text Color of the customer",
                                      help="Text color of the customer address")
    company_text_color = fields.Char(string="Company Text Color",
                                     help="Text color of the company address")
    logo_position = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                     string="Logo Position",
                                     help="The position of the company logo")
    customer_position = fields.Selection(
        [('left', 'Left'), ('right', 'Right')], string="Customer position",
        help="The position of the company address")
    company_position = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                        string="Company Address Position",
                                        help="The position of the company address")
    company_id = fields.Many2one('res.company', string='Company', index=True,
                                 default=lambda self: self.env.company,
                                 help="Current company")
