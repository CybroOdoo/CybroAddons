# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen @cybrosys(odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenseAutomatic Invoice And Posts/>.
#
#############################################################################
from odoo import models


class StockPicking(models.Model):
    """
    This class inherits from the `stock.picking` model in Odoo and adds
    functionality to automatically create and post invoices when a delivery is
    validated.
    """
    _inherit = 'stock.picking'

    def button_validate(self):
        """
        This function is called when a delivery is validated. It checks whether
        an invoice should be created and posted automatically based on
        configuration settings. If an invoice should be created, it calls
        the `_create_invoices` function on the sale associated with the
        delivery, creates the invoice, and posts it.
        If the `auto_send_invoice` configuration setting is enabled, it sends
        an email to the customer with the invoice attached.

        :return: result of the parent class's button_validate function
        """
        res = super().button_validate()
        auto_validate_invoice = self.env[
            'ir.config_parameter'].sudo().get_param(
            'automatic_invoice_and_post.is_create_invoice_delivery_validate')
        auto_send_invoice = self.env['ir.config_parameter'].sudo().get_param(
            'automatic_invoice_and_post.is_auto_send_invoice')
        if auto_validate_invoice:
            if any(rec.product_id.invoice_policy == 'delivery' for rec in
                   self.move_ids) or not self.sale_id.invoice_ids:
                # Call the _create_invoices function on the associated sale
                # to create the invoice
                invoice_created = self.sale_id._create_invoices(
                    self.sale_id) if self.sale_id else False
                # Post the created invoice
                if invoice_created:
                    invoice_created.action_post()
                    # If automatic invoice sending is enabled and the customer
                    # has an email address,send the invoice to the customer
                    if auto_send_invoice and invoice_created.partner_id.email:
                        template = self.env.ref(
                            'account.email_template_edi_invoice').sudo()
                        template.send_mail(invoice_created.id, force_send=True,
                                           email_values={
                                               'email_to': invoice_created.partner_id.email
                                           })
        return res
