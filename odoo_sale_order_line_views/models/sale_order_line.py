# -*- coding: utf-8 -*-
#############################################################################
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class SaleOrderLine(models.Model):
    """ Inherited class of sale order """
    _inherit = 'sale.order.line'

    order_line_image = fields.Binary(string="Image",
                                     related="product_id.image_128",
                                     help='Image of the ordered product')
    contact_email = fields.Char(related="order_partner_id.email",
                                string='Email',
                                help='Mail id of the customer')
    contact_phone = fields.Char(related="order_partner_id.phone",
                                help='Phone number of the customer',
                                string='Phone')
