# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#
# #############################################################################
from odoo import fields, models


class PosConfig(models.Model):
    """Inherited this module to add these boolean field"""
    _inherit = "pos.config"

    is_qr_code = fields.Boolean(string='Order QRCode',
                                help='Enable this field to show the '
                                     'qr code to pos receipt')
    is_invoice_number = fields.Boolean(string='Invoice Number',
                                       help='Enable this field to show the '
                                            'invoice number to pos receipt')
    is_customer_details = fields.Boolean(string='Customer Details',
                                         help='Enable this field to show the '
                                              'customer number to pos receipt')
    is_customer_name = fields.Boolean(string='Customer Name',
                                      help='Enable this field to show '
                                           'the customer name to pos receipt')
    is_customer_address = fields.Boolean(string='Customer Address',
                                         help='Enable this field to show '
                                              'the customer address code to '
                                              'pos receipt')
    is_customer_mobile = fields.Boolean(string='Customer Mobile',
                                        help='Enable this field to show the '
                                             'customer mobile to pos receipt')
    is_customer_phone = fields.Boolean(string='Customer Phone',
                                       help='Enable this field to show the '
                                            'customer phone to pos receipt')
    is_customer_email = fields.Boolean(string='Customer Email',
                                       help='Enable this field to show the '
                                            'customer email to pos receipt')
    is_customer_vat = fields.Boolean(string='Customer VAT',
                                     help='Enable this field to show the '
                                          'customer vat to pos receipt')
