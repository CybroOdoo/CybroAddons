# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PosOrderLines(models.Model):
    _inherit = 'pos.order'

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id

    currency_id = fields.Many2one('res.currency', string='Currency',
        required=True, readonly=True, default=_default_currency, track_visibility='always')

    @api.model
    def print_receipt(self):
        return {
            'type': 'ir.actions.client',
            'tag': 'aek_browser_pdf',
            'params': {
                'report_name': 'order_reprinting_pos.report_pos_reciept_new',
                'ids': self.ids,
                'datas': ["bjhg,jh"],
            }
        }

    @api.model
    def get_details(self, ref):
        order_id = self.env['pos.order'].sudo().search([('pos_reference', '=', ref)], limit=1)
        return order_id.ids

    @api.model
    def get_orderlines(self, ref):
        discount = 0
        result = []
        order_id = self.search([('pos_reference', '=', ref)], limit=1)
        lines = self.env['pos.order.line'].search([('order_id', '=', order_id.id)])
        payments = self.env['account.bank.statement.line'].search([('pos_statement_id', '=', order_id.id)])
        payment_lines = []
        change = 0
        for i in payments:
            if i.amount > 0:
                temp = {
                    'amount': i.amount,
                    'name': i.journal_id.name
                }
                payment_lines.append(temp)
            else:
                change += i.amount
        for line in lines:
            new_vals = {
                'product_id': line.product_id.name,
                'qty': line.qty,
                'price_unit': line.price_unit,
                'discount': line.discount,
                }
            discount += (line.price_unit * line.qty * line.discount) / 100
            result.append(new_vals)

        return [result, discount, payment_lines, change]
