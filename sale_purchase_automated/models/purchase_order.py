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


class PurchaseOrder(models.Model):
    """Inherit the 'purchase.order' model to confirm Purchase Orders
    and Print Bills when 'Confirm RFQ' and 'Print Bill' are enabled
    in Configuration Settings."""
    _inherit = 'purchase.order'

    automate_print_bills = fields.Boolean(
        string='Print Bills',
        help="Print bills for corresponding purchase orders")

    @api.model_create_multi
    def create(self, vals_list):
        """Super the method create to confirm RFQ"""
        # Call super to create records
        res = super().create(vals_list)

        # Get configuration parameters
        automate_purchase = self.env['ir.config_parameter'].sudo().get_bool(
            'automate_purchase')
        automate_print_bills = self.env['ir.config_parameter'].sudo().get_bool(
            'automate_print_bills')

        if automate_print_bills:
            res.automate_print_bills = True

        if automate_purchase:
            if not isinstance(vals_list, list):
                vals_list = [vals_list]

            # Process each record
            for idx, record in enumerate(res):
                vals = vals_list[idx] if idx < len(vals_list) else {}
                # Skip if it's a website order
                if vals.get('website_id'):
                    continue

                # Check order lines
                if record.order_line:
                    for line in record.order_line:
                        if line.product_id.invoice_policy == 'delivery':
                            raise ValidationError(
                                self.env._(
                                    "Please choose only ordered invoicing policy"))

                # Confirm the purchase order
                record.button_confirm()

        return res

    def action_print_bill(self):
        """Function to Print Bill"""
        return self.env.ref('account.account_invoices').report_action(
            self.invoice_ids)
