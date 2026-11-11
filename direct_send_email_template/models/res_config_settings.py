#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Inherit res.config.settings to add direct send email configuration."""

    _inherit = 'res.config.settings'

    is_direct_send_email_sale = fields.Boolean(
        string="Direct Send Email Sales",
        help="Enable to send direct emails for quotations and sales orders.",
        config_parameter="direct_send_email_template.is_direct_send_email_sale",
    )
    direct_send_mailtemplate_sq = fields.Many2one(
        comodel_name='mail.template',
        string='Quotation Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email template for sale quotations.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_sq",
    )
    direct_send_mailtemplate_so = fields.Many2one(
        comodel_name='mail.template',
        string='Sales Order Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email template for sales orders.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_so",
    )
    is_direct_send_email_purchase = fields.Boolean(
        string="Direct Send Email Purchases",
        help="Enable to send direct emails for requests for quotation and purchase orders.",
        config_parameter="direct_send_email_template.is_direct_send_email_purchase",
    )
    direct_send_mailtemplate_po = fields.Many2one(
        comodel_name='mail.template',
        string='Purchase Order Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email template for purchase orders.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_po",
    )
    direct_send_mailtemplate_prfq = fields.Many2one(
        comodel_name='mail.template',
        string='Request for Quotation Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email template for requests for quotation.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_prfq",
    )
    is_direct_send_email_account = fields.Boolean(
        string="Direct Send Email Invoices",
        help="Enable to send direct emails for invoices, bills, and credit notes.",
        config_parameter="direct_send_email_template.is_direct_send_email_account",
    )
    direct_send_mailtemplate_inv = fields.Many2one(
        comodel_name='mail.template',
        string='Invoice Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email template for customer invoices.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_inv",
    )
    direct_send_mailtemplate_credit = fields.Many2one(
        comodel_name='mail.template',
        string='Credit Note Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email template for customer credit notes.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_credit",
    )
    direct_send_mailtemplate_bill = fields.Many2one(
        comodel_name='mail.template',
        string='Vendor Bill Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email template for vendor bills.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_bill",
    )
    direct_send_mailtemplate_refund = fields.Many2one(
        comodel_name='mail.template',
        string='Vendor Refund Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email template for vendor refunds.',
        config_parameter="direct_send_email_template.direct_send_mailtemplate_refund",
    )
