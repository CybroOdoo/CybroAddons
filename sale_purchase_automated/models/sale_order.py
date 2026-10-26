# -*- coding: utf-8 -*-
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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    """Inherit the 'sale.order' model to confirm Sale Orders, Create Invoices,
    Validate Invoices, and Print Invoices when 'Confirm Quotation',
    'Create Invoice', 'Validate Invoice', and 'Print Invoices'
    are enabled in Configuration Settings."""
    _inherit = 'sale.order'

    automate_print_invoices = fields.Boolean(
        string='Print Invoices',
        help="Print invoices for corresponding sales orders")

    @api.model_create_multi
    def create(self, vals_list):
        """Super the method create to confirm quotation, create and validate
        invoice."""
        res = super().create(vals_list)
        automate_sale = self.env['ir.config_parameter'].sudo().get_bool(
            'automate_sale')
        automate_invoice = self.env['ir.config_parameter'].sudo().get_bool(
            'automate_invoice')
        automate_print_invoices = self.env[
            'ir.config_parameter'].sudo().get_bool('automate_print_invoices')
        automate_validate_invoice = self.env[
            'ir.config_parameter'].sudo().get_bool('automate_validate_invoice')
        if automate_print_invoices:
            res.automate_print_invoices = True
        if automate_sale:
            if not isinstance(vals_list, list):
                vals_list = [vals_list]
            for idx, order in enumerate(res):
                vals = vals_list[idx] if idx < len(vals_list) else {}
                if vals.get('website_id'):
                    continue
                if order.order_line:
                    if automate_invoice:
                        for line in order.order_line:
                            if line.product_id.invoice_policy == 'delivery':
                                raise ValidationError(
                                    self.env._(
                                        "Please choose only ordered invoicing policy"))
                    order.action_confirm()
                    if automate_invoice:
                        order._create_invoices()
                        if automate_validate_invoice:
                            order.invoice_ids.action_post()
                else:
                    order.action_confirm()
        return res

    def action_print_invoice(self):
        """Method to print invoice"""
        return self.env.ref('account.account_invoices').report_action(
            self.invoice_ids)
