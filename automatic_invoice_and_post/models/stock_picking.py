
# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Sreerag PM @cybrosys(odoo@cybrosys.com)
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
        done_pickings = self.filtered(
            lambda p: p.state == 'done' and p.picking_type_code == 'outgoing' and p.sale_id
        )
        if not done_pickings:
            return res

        sale_orders = done_pickings.mapped('sale_id').filtered(
            lambda so: so.state == 'sale' and so.invoice_status == 'to invoice'
        )
        if not sale_orders:
            return res

        invoices = sale_orders.with_context(
            raise_if_nothing_to_invoice=False
        )._create_invoices()

        draft_invoices = invoices.filtered(lambda inv: inv.state == 'draft')
        if draft_invoices:
            draft_invoices.action_post()

        if auto_send_invoice and draft_invoices:
            template = self.env.ref('account.email_template_edi_invoice').sudo()
            for invoice in draft_invoices.filtered(lambda inv: inv.partner_id.email):
                template.send_mail(
                    invoice.id,
                    force_send=True,
                    email_values={'email_to': invoice.partner_id.email},
                )

        return res
