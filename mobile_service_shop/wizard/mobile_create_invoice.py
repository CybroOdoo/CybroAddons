# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time

from odoo import api, fields, models, _
from odoo.exceptions import Warning, UserError


class MobileServiceInvoice(models.Model):

    _name = 'mobile.invoice'

    advance_payment_method = fields.Selection([('advance', 'Advance'), ('full_amount', 'Full amount')],
                                              string='Invoice method', default='advance')
    amount = fields.Integer(string='Amount')
    number = fields.Char(string='Service Id')

    @api.multi
    def action_invoice_create(self):
        active_id = self._context.get('active_id')
        service_id = self.env['mobile.service'].search([('id', '=', active_id)])
        if not service_id.env['product.product'].search([("name", "=", "Mobile Service Advance")]):
            vals = self._prepare_advance_product()
            self.env['product.product'].create(vals)

        if not service_id.env['product.product'].search([("name", "=", "Mobile Service Charge")]):
            vals1 = self._prepare_service_product()
            self.env['product.product'].create(vals1)

        service_id.first_invoice_created = True
        inv_obj = self.env['account.invoice']
        inv_line_obj = self.env['account.invoice.line']
        supplier = service_id.person_name
        inv_data = {
            'name': supplier.name,
            'type': 'out_invoice',
            'reference': supplier.name,
            'account_id': supplier.property_account_receivable_id.id,
            'partner_id': supplier.id,
            'currency_id': service_id.company_id.currency_id.id,
            'journal_id': service_id.journal_type.id,
            'origin': service_id.name,
            'company_id': service_id.company_id.id,
            'date_due': service_id.return_date,
        }
        inv_id = inv_obj.create(inv_data)
        service_id.first_payment_inv = inv_id.id
        self.number = service_id.name
        if self.advance_payment_method != 'advance':
            product_id = service_id.env['product.product'].search([("name", "=", "Mobile Service Charge")])
        else:
            product_id = service_id.env['product.product'].search([("name", "=", "Mobile Service Advance")])

        if product_id.property_account_income_id.id:
            income_account = product_id.property_account_income_id.id
        elif product_id.categ_id.property_account_income_categ_id.id:
            income_account = product_id.categ_id.property_account_income_categ_id.id
        else:
            raise UserError('Please define income account for this product: "%s" (id:%d).' %
                            (product_id.name, product_id.id))
        flag = 0
        if self.amount:
            flag = 1
            inv_line_data = {
                'name': product_id.name,
                'account_id': income_account,
                'price_unit': self.amount,
                'quantity': 1,
                'product_id': product_id.id,
                'invoice_id': inv_id.id,
            }
            inv_line_obj.create(inv_line_data)

        sale_order_product = self.env['product.order.line'].search([('product_order_id', '=', service_id.name)])
        for line_data in sale_order_product:
            qty = line_data.product_uom_qty - line_data.qty_invoiced
            if line_data.product_uom_qty < line_data.qty_invoiced:
                raise UserError(_('Used quantity is less than invoiced quantity'))
            uom_id = line_data.product_id.product_tmpl_id.uom_id
            if qty > 0:
                flag = 1
                price = line_data.product_id.list_price
                inv_line_data = {
                    'name': line_data.product_id.name,
                    'account_id': income_account,
                    'price_unit': price,
                    'quantity': qty,
                    'uom_id': uom_id.id,
                    'product_id': line_data.product_id.id,
                    'invoice_id': inv_id.id,
                }
                inv_line_obj.create(inv_line_data)
                line_data.qty_invoiced = line_data.qty_invoiced + qty

        # inv_id.action_invoice_open()
        if flag != 1:
            raise UserError(_('Nothing to create invoice'))
        imd = service_id.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': 'ir.actions.act_window',
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': 'account.invoice',
        }
        if len(inv_id) > 1:
            result['domain'] = "[('id','in',%s)]" % inv_id.ids
        elif len(inv_id) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = inv_id.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    def _prepare_advance_product(self):
        return {
            'name': 'Mobile Service Advance',
            'type': 'service',
            'invoice_policy': 'order',
            'company_id': False,
        }

    def _prepare_service_product(self):
        return {
            'name': 'Mobile Service Charge',
            'type': 'service',
            'invoice_policy': 'order',
            'company_id': False,
        }
