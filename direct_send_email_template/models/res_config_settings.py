# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC
#    LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import fields, models


class ResConfig(models.TransientModel):
    """ Inherit the base settings to add a direct send email
     configuration fields. """
    _inherit = 'res.config.settings'

    is_direct_send_email_sale = fields.Boolean(
        string="Direct Send Email Sale",
        help="Enable to send direct email for sale/quotations.",
        config_parameter="direct_send_email_template.is_direct_send_email_sale")
    direct_send_mailtemplate_sq = fields.Many2one(
        comodel_name='mail.template', string='Quotation Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email Template for Sale Quotation.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_sq")
    direct_send_mailtemplate_so = fields.Many2one(
        comodel_name='mail.template', string='Sales Order Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email Template for Sale Order.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_so")
    is_direct_send_email_purchase = fields.Boolean(
        string="Direct Send Email Purchase",
        help="Enable to send direct email for purchase/rfqs.",
        config_parameter="direct_send_email_template.is_direct_send_email_purchase")
    direct_send_mailtemplate_po = fields.Many2one(
        comodel_name='mail.template', string='Purchase Order Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email Template for Purchase Order.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_po")
    direct_send_mailtemplate_prfq = fields.Many2one(
        comodel_name='mail.template',
        string='Request for Quotation Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email Template for Request For Quotation.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_prfq")
    is_direct_send_email_account = fields.Boolean(
        string="Direct Send Email Invoice.",
        help="Enable to send direct email for invoices.",
        config_parameter="direct_send_email_template.is_direct_send_email_account")
    direct_send_mailtemplate_inv = fields.Many2one(
        comodel_name='mail.template', string='Invoice Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Customer Invoice.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_inv")
    direct_send_mailtemplate_credit = fields.Many2one(
        comodel_name='mail.template', string='Credit note Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Customer Credit Note.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_credit")
    direct_send_mailtemplate_bill = fields.Many2one(
        comodel_name='mail.template', string='Bills Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Vendor Bill.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_bill")
    direct_send_mailtemplate_refund = fields.Many2one(
        comodel_name='mail.template', string='Refund Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Vendor Refund.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_refund")
