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
#############################################################################
from odoo import api, fields, models


class ResConfig(models.TransientModel):
    """ Inherit the base settings to add a direct send email configuration fields """
    _inherit = 'res.config.settings'

    is_direct_send_email_sale = fields.Boolean(string="Direct Send Email Sale")
    direct_send_mailtemplate_sq_id = fields.Many2one(
        comodel_name='mail.template', string='Quotation Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email Template for Sale Quoatation')
    direct_send_mailtemplate_so_id = fields.Many2one(
        comodel_name='mail.template', string='Sales Order Email Template',
        domain="[('model', '=', 'sale.order')]",
        help='Email Template for Sale Order')
    is_direct_send_email_purchase = fields.Boolean(string="Direct Send Email Purchase")
    direct_send_mailtemplate_po_id = fields.Many2one(
        comodel_name='mail.template', string='Purchase Order Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email Template for Purchase Order')
    direct_send_mailtemplate_prfq_id = fields.Many2one(
        comodel_name='mail.template',
        string='Request for Quotation Email Template',
        domain="[('model', '=', 'purchase.order')]",
        help='Email Template for Request For Quotation')
    is_direct_send_email_account = fields.Boolean(string="Direct Send Email Invoice")
    direct_send_mailtemplate_inv_id = fields.Many2one(
        comodel_name='mail.template', string='Invoice Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Customer Invoice')
    direct_send_mailtemplate_credit_id = fields.Many2one(
        comodel_name='mail.template', string='Credit note Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Customer Credit Note')
    direct_send_mailtemplate_bill_id = fields.Many2one(
        comodel_name='mail.template', string='Bills Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Vendor Bill')
    direct_send_mailtemplate_refund_id = fields.Many2one(
        comodel_name='mail.template', string='Refund Email Template',
        domain="[('model', '=', 'account.move')]",
        help='Email Template for Vendor Refund')

    def set_values(self):
        """ save values in the settings direct send email fields"""
        super(ResConfig, self).set_values()
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.is_direct_send_email_sale',
            self.is_direct_send_email_sale)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_sq_id',
            self.direct_send_mailtemplate_sq_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_so_id',
            self.direct_send_mailtemplate_so_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.is_direct_send_email_purchase',
            self.is_direct_send_email_purchase)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_prfq_id',
            self.direct_send_mailtemplate_prfq_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_po_id',
            self.direct_send_mailtemplate_po_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.is_direct_send_email_account',
            self.is_direct_send_email_account)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_inv_id',
            self.direct_send_mailtemplate_inv_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_credit_id',
            self.direct_send_mailtemplate_credit_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_bill_id',
            self.direct_send_mailtemplate_bill_id.id)
        self.env['ir.config_parameter'].set_param(
            'direct_send_email_template.direct_send_mailtemplate_refund_id',
            self.direct_send_mailtemplate_refund_id.id)

    @api.model
    def get_values(self):
        """ Get values for direct send email fields in the settings
         and assign the value to that fields"""
        res = super(ResConfig, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            is_direct_send_email_sale=params.get_param(
                'direct_send_email_template.is_direct_send_email_sale'),
            direct_send_mailtemplate_sq_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_sq_id')),
            direct_send_mailtemplate_so_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_so_id')),
            is_direct_send_email_purchase=params.get_param(
                'direct_send_email_template.is_direct_send_email_purchase'),
            direct_send_mailtemplate_po_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_po_id')),
            direct_send_mailtemplate_prfq_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_prfq_id')),
            is_direct_send_email_account=params.get_param(
                'direct_send_email_template.is_direct_send_email_account'),
            direct_send_mailtemplate_inv_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_inv_id')),
            direct_send_mailtemplate_credit_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_credit_id')),
            direct_send_mailtemplate_bill_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_bill_id')),
            direct_send_mailtemplate_refund_id=int(
                params.get_param('direct_send_email_template.direct_send_mailtemplate_refund_id')),
        )
        return res
