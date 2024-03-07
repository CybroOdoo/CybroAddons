# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
    def create(self, vals):
        """Super the method create to confirm RFQ"""
        res = super(PurchaseOrder, self).create(vals)
        automate_purchase = self.env['ir.config_parameter'].sudo().get_param(
            'automate_purchase')
        automate_print_bills = self.env['ir.config_parameter'].sudo().get_param(
            'automate_print_bills')
        if automate_purchase:
            for rec in vals.get('order_line'):
                product = self.env['product.product'].search(
                    [('id', '=', rec[2].get('product_id'))])
                if product.invoice_policy == 'delivery':
                    raise ValidationError(
                        _("Please choose only ordered invoicing policy"))
                else:
                    res.button_confirm()
            if automate_print_bills:
                res.automate_print_bills = True
            return res
        else:
            return res

    def action_print_bill(self):
        """Function to Print Bill"""
        return self.env.ref('account.account_invoices').report_action(
            self.invoice_ids)
