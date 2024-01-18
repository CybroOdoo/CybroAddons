# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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


class MailTemplate(models.Model):
    """Inherited this model for adding some fields that help to check the
        message template is a delivery, invoice, purchase, or sale order
        template """
    _inherit = 'mail.template'

    is_delivery_template = fields.Boolean(string='Delivery Template',
                                          help="To check the message template"
                                               " for sending delivery "
                                               "to whatsapp")
    is_invoice_template = fields.Boolean(string='Invoice Template',
                                         help="To check the message template "
                                              "for sending delivery "
                                              "to whatsapp")
    is_purchase_template = fields.Boolean(string="Purchase Template",
                                          help="To check the message template "
                                               "sending purchase order to"
                                               " whatsapp")
    is_sale_template = fields.Boolean(string="Sale Template",
                                      help="To check the message template for"
                                           "sending sale order to whatsapp")
