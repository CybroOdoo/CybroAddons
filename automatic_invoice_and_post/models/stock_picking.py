# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Afra K (odoo@cybrosys.com)
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
from odoo import models

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        res = super().button_validate()
        auto_validate_invoice = self.env['ir.config_parameter'].sudo().get_param('automatic_invoice_and_post.is_create_invoice_delivery_validate')
        auto_send_invoice = self.env['ir.config_parameter'].sudo().get_param('automatic_invoice_and_post.is_auto_send_invoice')

        if auto_validate_invoice and self.sale_id:
            try:
                # Check for order lines with delivered quantities or backorders
                if self.all_order_lines_matched() or self.has_backorders_with_deliveries():
                    invoice = self.sale_id._create_invoices(self.sale_id)
                    invoice.action_post()  # Post the created invoice
                    self.sale_id.invoice_ids += invoice

                    # Send invoice if enabled
                    if auto_send_invoice and invoice.partner_id.email:
                        template = self.env.ref('account.email_template_edi_invoice').sudo()
                        template.send_mail(invoice.id, force_send=True, email_values={'email_to': invoice.partner_id.email})

            except Exception:
                pass  # Optionally handle the exception as needed

        return res

    def all_order_lines_matched(self):
        """ Check if all order lines have matching ordered and delivered quantities. """
        return all(line.product_uom_qty == line.qty_delivered for line in self.sale_id.order_line)

    def has_backorders_with_deliveries(self):
        """ Check if there are delivered items that also have backorders. """
        return any(line.qty_delivered > 0 and line.product_uom_qty > line.qty_delivered for line in self.sale_id.order_line)
