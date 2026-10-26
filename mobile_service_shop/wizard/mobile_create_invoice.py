# -*- coding: utf-8 -*-
"""Wizard for creating mobile service customer invoices."""
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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import fields, models
from odoo.exceptions import UserError


class MobileInvoice(models.TransientModel):
    """Model for managing the creation of invoices in mobile service
     operations."""
    _name = 'mobile.invoice.wizard'
    _description = 'Mobile Invoice'

    advance_payment_method = fields.Selection(
        [('advance', 'Advance'), ('full_amount', 'Full amount')],
        string='Invoice method', default='advance')
    amount = fields.Float(string='Invoice Amount', help="Payment Amount")
    number = fields.Char(string='Service Id', help="Payment service id")
    company_id = fields.Many2one('res.company',
                                 help="Company associated with this invoice.",
                                 default=lambda self: self.env.company, required=True)

    def _prepare_fee_invoice_line(self):
        """Prepare service fee invoice line if amount is specified."""
        if self.amount <= 0:
            return None

        if self.advance_payment_method == 'advance':
            tmpl_xml_id = 'mobile_service_shop.mobile_service_advance_product'
        else:
            tmpl_xml_id = 'mobile_service_shop.mobile_service_product'

        product_tmpl = self.env.ref(tmpl_xml_id, raise_if_not_found=False)
        product = product_tmpl.product_variant_id if product_tmpl else False
        if not product:
            raise UserError(self.env._("The required service product could not be found."))

        return {
            'product_id': product.id,
            'name': product.display_name or product.name,
            'quantity': 1.0,
            'price_unit': self.amount,
            'product_uom_id': product.uom_id.id if product.uom_id else False,
        }

    def _prepare_part_invoice_lines(self, service_id):
        """Prepare part invoice lines and return lines with records to update."""
        part_lines = []
        lines_to_update = []
        parts = self.env['product.order.line'].search([
            ('product_order_id', '=', service_id.id)
        ])
        for line_data in parts:
            if line_data.product_uom_qty < line_data.qty_invoiced:
                raise UserError(self.env._(
                    'Used quantity is less than invoiced quantity for part "%s".',
                    line_data.product_id.display_name
                ))
            qty = line_data.product_uom_qty - line_data.qty_invoiced
            if qty > 0:
                uom_id = line_data.product_id.uom_id.id if line_data.product_id.uom_id else False
                part_lines.append({
                    'product_id': line_data.product_id.id,
                    'name': line_data.product_id.display_name or line_data.product_id.name,
                    'quantity': qty,
                    'price_unit': line_data.price_unit,
                    'product_uom_id': uom_id,
                })
                lines_to_update.append((line_data, qty))
        return part_lines, lines_to_update

    def action_invoice_create(self):
        """Creating invoice for the mobile service."""
        active_id = self.env.context.get('active_id')
        service_id = self.env['mobile.service'].browse(active_id)
        if not service_id or not service_id.exists():
            raise UserError(self.env._("No mobile service record found to create an invoice."))

        supplier = service_id.person_name
        if not supplier:
            raise UserError(self.env._("Please assign a customer to the service before invoicing."))

        invoice_lines = []
        fee_line = self._prepare_fee_invoice_line()
        if fee_line:
            invoice_lines.append((0, 0, fee_line))

        part_lines, lines_to_update = self._prepare_part_invoice_lines(service_id)
        for part_line in part_lines:
            invoice_lines.append((0, 0, part_line))

        if not invoice_lines:
            raise UserError(self.env._('Nothing to create invoice.'))

        inv_data = {
            'move_type': 'out_invoice',
            'partner_id': supplier.id,
            'currency_id': service_id.company_id.currency_id.id,
            'invoice_origin': service_id.name,
            'company_id': service_id.company_id.id,
            'invoice_line_ids': invoice_lines,
        }
        if service_id.journal_type:
            inv_data['journal_id'] = service_id.journal_type.id

        inv_id = self.env['account.move'].create(inv_data)
        service_id.first_invoice_created = True
        if not service_id.first_payment_inv:
            service_id.first_payment_inv = inv_id.id
        self.number = service_id.name

        for line_data, qty in lines_to_update:
            line_data.qty_invoiced += qty

        return {
            'name': self.env._('Customer Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': inv_id.id,
            'target': 'current',
        }
