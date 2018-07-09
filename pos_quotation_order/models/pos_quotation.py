# -*- coding: utf-8 -*-

import logging
import psycopg2
from functools import partial
from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    quot_ref = fields.Many2one('pos.quotation', string='Quotation Ref')

    @api.model
    def create_from_ui(self, orders):
        # Keep only new orders
        submitted_references = [o['data']['name'] for o in orders]
        pos_order = self.search([('pos_reference', 'in', submitted_references)])
        existing_orders = pos_order.read(['pos_reference'])
        existing_references = set([o['pos_reference'] for o in existing_orders])
        orders_to_save = [o for o in orders if o['data']['name'] not in existing_references]
        order_ids = []
        quot_ids = []

        for tmp_order in orders_to_save:
            to_invoice = tmp_order['to_invoice']
            order = tmp_order['data']
            if to_invoice:
                self._match_payment_to_invoice(order)
            pos_order = self._process_order(order)
            if pos_order.quot_ref:
                pos_order.quot_ref.write({'state': 'confirmed'})
                quot_ids.append(pos_order.quot_ref.id)
            order_ids.append(pos_order.id)

            try:
                pos_order.action_pos_order_paid()
            except psycopg2.OperationalError:
                # do not hide transactional errors, the order(s) won't be saved!
                raise
            except Exception as e:
                _logger.error('Could not fully process the POS Order: %s', tools.ustr(e))

            if to_invoice:
                pos_order.action_pos_order_invoice()
                pos_order.invoice_id.sudo().action_invoice_open()
                pos_order.account_move = pos_order.invoice_id.move_id
        return order_ids, quot_ids

    @api.model
    def _order_fields(self, ui_order):
        process_line = partial(self.env['pos.order.line']._order_line_fields)
        quot_id = False
        if 'quotation_ref' in ui_order:
            if ui_order['quotation_ref']:
                quot_id = ui_order['quotation_ref']['id']
        return {
            'name': ui_order['name'],
            'quot_ref': quot_id,
            'user_id': ui_order['user_id'] or False,
            'session_id': ui_order['pos_session_id'],
            'lines': [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'pos_reference': ui_order['name'],
            'partner_id': ui_order['partner_id'] or False,
            'date_order': ui_order['creation_date'],
            'fiscal_position_id': ui_order['fiscal_position_id']
        }


class PosQuotation(models.Model):
    _name = 'pos.quotation'

    @api.model
    def _amount_line_tax(self, line, fiscal_position_id):
        taxes = line.tax_ids.filtered(lambda t: t.company_id.id == line.order_id.company_id.id)
        if fiscal_position_id:
            taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
        price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
        taxes = taxes.compute_all(price, line.order_id.pricelist_id.currency_id, line.qty, product=line.product_id,
                                  partner=line.order_id.partner_id or False)['taxes']
        return sum(tax.get('amount', 0.0) for tax in taxes)

    @api.model
    def _order_fields(self, ui_order):
        process_line = partial(self.env['pos.quotation.line']._order_line_fields)
        return {
            'lines': [process_line(l) for l in ui_order['lines']] if ui_order['lines'] else False,
            'partner_id': ui_order['partner_id'] or False,
            'date_order': ui_order['date_order'],
            'note': ui_order['note'] or '',
        }

    def _default_session(self):
        return self.env['pos.session'].search([('state', '=', 'opened'), ('user_id', '=', self.env.uid)], limit=1)

    def _default_pricelist(self):
        return self._default_session().config_id.pricelist_id

    name = fields.Char(string='Order Ref', required=True, readonly=True, copy=False, default='/')
    company_id = fields.Many2one('res.company', string='Company', required=True, readonly=True,
                                 default=lambda self: self.env.user.company_id)
    date_quotation = fields.Datetime(string='Quotation Date', readonly=True, index=True, default=fields.Datetime.now)
    date_order = fields.Date(string='Order Date', readonly=True, index=True)
    amount_tax = fields.Float(compute='_compute_amount_all', string='Taxes', digits=0)
    amount_total = fields.Float(compute='_compute_amount_all', string='Total', digits=0)
    lines = fields.One2many('pos.quotation.line', 'order_id', string='Order Lines', copy=True)
    pricelist_id = fields.Many2one('product.pricelist', string='Pricelist', default=_default_pricelist)
    partner_id = fields.Many2one('res.partner', string='Customer', change_default=True, index=True)
    state = fields.Selection([('draft', 'New'), ('confirmed', 'Confirmed')], 'Status', readonly=True, copy=False, default='draft')
    note = fields.Text(string='Internal Notes')
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position')

    @api.depends('lines.price_subtotal_incl', 'lines.discount')
    def _compute_amount_all(self):
        for order in self:
            order.amount_tax = 0.0
            currency = order.pricelist_id.currency_id
            order.amount_tax = currency.round(
                sum(self._amount_line_tax(line, order.fiscal_position_id) for line in order.lines))
            amount_untaxed = currency.round(sum(line.price_subtotal for line in order.lines))
            order.amount_total = order.amount_tax + amount_untaxed

    @api.model
    def create_from_ui(self, orders):
        order_id = self.create(self._order_fields(orders))
        order = {'id': order_id.id,
                 'name': order_id.name}
        return order

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('pos.quotation') or '/'
        return super(PosQuotation, self).create(vals)


class PosQuotationLine(models.Model):
    _name = "pos.quotation.line"
    _description = "Lines of Point of Sale"
    _rec_name = "product_id"

    def _order_line_fields(self, line):
        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]
        return line

    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    name = fields.Char(string='Line No')
    notice = fields.Char(string='Discount Notice')
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)],
                                 required=True, change_default=True)
    price_unit = fields.Float(string='Unit Price', digits=0)
    qty = fields.Float('Quantity', default=1)
    price_subtotal = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal w/o Tax')
    price_subtotal_incl = fields.Float(compute='_compute_amount_line_all', digits=0, string='Subtotal')
    discount = fields.Float(string='Discount (%)', digits=0, default=0.0)
    order_id = fields.Many2one('pos.quotation', string='Order Ref', ondelete='cascade')
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    tax_ids = fields.Many2many('account.tax', string='Taxes', readonly=True)
    tax_ids_after_fiscal_position = fields.Many2many('account.tax',string='Taxes')
    pack_lot_ids = fields.One2many('pos.pack.operation.lot', 'pos_order_line_id', string='Lot/serial Number')

    @api.depends('price_unit', 'tax_ids', 'qty', 'discount', 'product_id')
    def _compute_amount_line_all(self):
        for line in self:
            currency = line.order_id.pricelist_id.currency_id
            taxes = line.tax_ids.filtered(lambda tax: tax.company_id.id == line.order_id.company_id.id)
            fiscal_position_id = line.order_id.fiscal_position_id
            if fiscal_position_id:
                taxes = fiscal_position_id.map_tax(taxes, line.product_id, line.order_id.partner_id)
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            line.price_subtotal = line.price_subtotal_incl = price * line.qty
            if taxes:
                taxes = taxes.compute_all(price, currency, line.qty, product=line.product_id,
                                          partner=line.order_id.partner_id or False)
                line.price_subtotal = taxes['total_excluded']
                line.price_subtotal_incl = taxes['total_included']

            line.price_subtotal = currency.round(line.price_subtotal)
            line.price_subtotal_incl = currency.round(line.price_subtotal_incl)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(
                    _('You have to select a pricelist in the sale form !\n'
                      'Please set one before choosing a product.'))
            price = self.order_id.pricelist_id.get_product_price(
                self.product_id, self.qty or 1.0, self.order_id.partner_id)
            self._onchange_qty()
            self.price_unit = price
            self.tax_ids = self.product_id.taxes_id

    @api.onchange('qty', 'discount', 'price_unit', 'tax_ids')
    def _onchange_qty(self):
        if self.product_id:
            if not self.order_id.pricelist_id:
                raise UserError(_('You have to select a pricelist in the sale form !'))
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
            self.price_subtotal = self.price_subtotal_incl = price * self.qty
            if self.product_id.taxes_id:
                taxes = self.product_id.taxes_id.compute_all(price, self.order_id.pricelist_id.currency_id, self.qty,
                                                             product=self.product_id, partner=False)
                self.price_subtotal = taxes['total_excluded']
                self.price_subtotal_incl = taxes['total_included']
