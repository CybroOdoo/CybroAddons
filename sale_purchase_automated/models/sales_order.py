# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2020-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Nimisha Muralidhar (odoo@cybrosys.com)
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
from odoo import models, _, api, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    automate_print_invoices = fields.Boolean('Print Invoices', help="Print invoices for corresponding purchase orders")

    @api.model_create_multi
    def create(self, vals_list):
        """
            Super the method create to confirm quotation,create and validate invoice.
        """
        res = super(SaleOrder, self).create(vals_list)
        automate_purchase = self.env['ir.config_parameter'].sudo().get_param('automate_sale')
        automate_invoice = self.env['ir.config_parameter'].sudo().get_param('automate_invoice')
        automate_print_invoices = self.env['ir.config_parameter'].sudo().get_param('automate_print_invoices')
        automate_validate_voice = self.env['ir.config_parameter'].sudo().get_param('automate_validate_voice')
        if automate_print_invoices != False:
            res.automate_print_invoices = True
        if automate_purchase != False:
            res.action_confirm()
            if automate_invoice != False:
                res._create_invoices()
                if automate_validate_voice != False:
                    res.invoice_ids.action_post()
        return res

    def action_print_invoice(self):
        """
        Method to print invoice.
        """
        data = self.invoice_ids
        return self.env.ref('account.account_invoices').report_action(data)
