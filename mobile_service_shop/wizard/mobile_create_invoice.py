# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Milind Mohan @ Cybrosys, (odoo@cybrosys.com)
#            Mohammed Shahil M P @ Cybrosys, (odoo@cybrosys.com)
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
from odoo.exceptions import Warning, UserError
from odoo.exceptions import UserError, ValidationError


class MobileServiceInvoice(models.Model):

    _name = 'mobile.invoice'

    advance_payment_method = fields.Selection([('advance', 'Advance'), ('full_amount', 'Full amount')],
                                              string='Invoice method', default='advance')
    amount = fields.Integer(string='Amount')
    number = fields.Char(string='Service Id')

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
        inv_obj = self.env['account.move']
        inv_line_obj = self.env['account.move.line']
        supplier = service_id.person_name
        inv_data = {
            'move_type': 'out_invoice',
            'ref': supplier.name,
            'partner_id': supplier.id,
            'currency_id': service_id.company_id.currency_id.id,
            'journal_id': service_id.journal_type.id,
            'invoice_origin': service_id.name,
            'company_id': service_id.company_id.id,
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
            inv_line_data = [(0, 0, {
                'name': product_id.name,
                'price_unit': self.amount,
                'quantity': 1,
                'credit': self.amount,
                'debit': 0,
                'account_id': income_account,
                'product_id': product_id.id,
                'move_id': inv_id.id,
            })]
            inv_id.write({
                'invoice_line_ids': inv_line_data})
            inv_id._recompute_payment_terms_lines()

        sale_order_product = self.env['product.order.line'].search([('product_order_id', '=', service_id.name)])
        for line_data in sale_order_product:
            qty = line_data.product_uom_qty - line_data.qty_invoiced
            if line_data.product_uom_qty < line_data.qty_invoiced:
                raise UserError(_('Used quantity is less than invoiced quantity'))
            uom_id = line_data.product_id.product_tmpl_id.uom_id
            if qty > 0:
                flag = 1
                price = line_data.product_id.list_price
                inv_line_data = [(0, 0, {
                    'name': line_data.product_id.name,
                    'price_unit': price,
                    'quantity': qty,
                    'product_uom_id': uom_id.id,
                    'credit': price,
                    'debit': 0,
                    'account_id': income_account,
                    'product_id': line_data.product_id.id,
                    'move_id': inv_id.id,
                })]
                inv_id.write({
                    'invoice_line_ids': inv_line_data})
                line_data.qty_invoiced = line_data.qty_invoiced + qty
                inv_id._recompute_payment_terms_lines()

        inv_id.post()
        if flag != 1:
            raise UserError(_('Nothing to create invoice'))
        imd = service_id.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_move_out_invoice_type')
        list_view_id = imd.xmlid_to_res_id('account.view_move_tree')
        form_view_id = imd.xmlid_to_res_id('account.view_move_form')
        result = {
            'name': action.name,
            'help': action.help,
            'type': 'ir.actions.act_window',
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                      [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': 'account.move',
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
