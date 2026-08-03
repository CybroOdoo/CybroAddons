# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    """Inherit the 'purchase_order' model to confirm Purchase Orders
    and Print Bills when 'Confirm RFQ' and 'Print Bill' are enabled
    in Configuration Settings."""
    _inherit = 'purchase.order'

    automate_print_bills = fields.Boolean(
        string='Create Bills', help="Create bills with purchase orders")

    @api.model
    def create(self, vals_list):
        """Super the method create to confirm RFQ"""
        # Call super to create records
        res = super(PurchaseOrder, self).create(vals_list)

        # Get configuration parameters
        automate_purchase = self.env['ir.config_parameter'].sudo().get_param(
            'automate_purchase')
        automate_print_bills = self.env['ir.config_parameter'].sudo().get_param(
            'automate_print_bills')

        if automate_purchase:
            # Ensure vals_list is a list
            if not isinstance(vals_list, list):
                vals_list = [vals_list]

            # Process each record
            for idx, vals in enumerate(vals_list):
                # Skip if it's a website order
                if vals.get('website_id'):
                    continue

                # Get the corresponding created record
                record = res[idx] if len(res) > 1 else res

                # Check order lines
                order_lines = vals.get('order_line', [])
                if order_lines:
                    for line in order_lines:
                        # Handle One2many format: (0, 0, {values}) or (1, id, {values})
                        if isinstance(line, (list, tuple)) and len(line) >= 3:
                            line_vals = line[2] if isinstance(line[2], dict) else {}
                            product_id = line_vals.get('product_id')
                        elif isinstance(line, dict):
                            product_id = line.get('product_id')
                        else:
                            continue

                        if product_id:
                            product = self.env['product.product'].browse(product_id)
                            if product.invoice_policy == 'delivery':
                                raise ValidationError(
                                    _("Please choose only ordered invoicing policy"))

                    # Confirm the purchase order
                    record.button_confirm()

                    # Set automate_print_bills flag
                    if automate_print_bills:
                        record.automate_print_bills = True

        return res

    def action_print_bill(self):
        """Function to Print Bill"""
        return self.env.ref('account.account_invoices').report_action(
            self.invoice_ids)
