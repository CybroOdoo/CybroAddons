# -*- coding: utf-8 -*-

from openerp import SUPERUSER_ID
from openerp.osv import osv
from openerp.tools import float_is_zero

from openerp.exceptions import UserError
from openerp import api, fields, models, _
import openerp.addons.decimal_precision as dp


class PosInvoiceReportNew(osv.AbstractModel):
    _name = 'report.discounts_in_pos.report_invoice'

    def render_html(self, cr, uid, ids, data=None, context=None):
        report_obj = self.pool['report']
        posorder_obj = self.pool['pos.order']
        report = report_obj._get_report_from_name(cr, uid, 'discounts_in_pos.report_invoice')
        selected_orders = posorder_obj.browse(cr, uid, ids, context=context)
        ids_to_print = []
        invoiced_posorders_ids = []
        for order in selected_orders:
            if order.invoice_id:
                ids_to_print.append(order.invoice_id.id)
                invoiced_posorders_ids.append(order.id)

        not_invoiced_orders_ids = list(set(ids) - set(invoiced_posorders_ids))
        if not_invoiced_orders_ids:
            not_invoiced_posorders = posorder_obj.browse(cr, uid, not_invoiced_orders_ids, context=context)
            not_invoiced_orders_names = list(map(lambda a: a.name, not_invoiced_posorders))
            raise UserError(_('No link to an invoice for %s.') % ', '.join(not_invoiced_orders_names))

        docargs = {
            'docs': self.pool['account.invoice'].browse(cr, uid, ids_to_print, context=context)
        }

        return report_obj.render(cr, SUPERUSER_ID, ids, 'discounts_in_pos.report_invoice', docargs, context=context)


class POSInvoiceNew(models.Model):
    _inherit = 'account.invoice.line'

    discount_fixed = fields.Float(string='Discount.Fixed', digits=dp.get_precision('DiscountFixed'),
                            default=0.0)

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity',
                 'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id', 'invoice_id.company_id')
    def _compute_price(self):
        super(POSInvoiceNew, self)._compute_price()

        currency = self.invoice_id and self.invoice_id.currency_id or None

        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        if self.discount != 0:
            price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        if self.discount_fixed != 0:
            price = self.price_unit
        taxes = False
        if self.invoice_line_tax_ids:
            taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                          partner=self.invoice_id.partner_id)

        self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price

        if self.discount != 0:
            self.price_subtotal = price_subtotal_signed = taxes['total_excluded'] if taxes else self.quantity * price

        if self.discount_fixed != 0:
            self.price_subtotal = price_subtotal_signed = taxes[
                'total_excluded'] if taxes else self.quantity * price - self.discount_fixed
        if self.invoice_id.currency_id and self.invoice_id.currency_id != self.invoice_id.company_id.currency_id:
            price_subtotal_signed = self.invoice_id.currency_id.compute(price_subtotal_signed,
                                                                        self.invoice_id.company_id.currency_id)
        sign = self.invoice_id.type in ['in_refund', 'out_refund'] and -1 or 1
        self.price_subtotal_signed = price_subtotal_signed * sign


class POSInvoiceTotalDisc(models.Model):
    _inherit = 'account.invoice'

    discount_total = fields.Float(string='Total Discount', default=0.0)
    discount_percent = fields.Float(string='Total Discount(%)', default=0.0)

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'currency_id', 'company_id')
    def _compute_amount(self):
        super(POSInvoiceTotalDisc, self)._compute_amount()
        self.amount_total = self.amount_untaxed + self.amount_tax
        if self.discount_total > 0:
            self.amount_total -= self.discount_total
        if self.discount_percent > 0:
            self.amount_total -= ((self.amount_untaxed + self.amount_tax) * self.discount_percent / 100)

    def _compute_residual(self):
        super(POSInvoiceTotalDisc, self)._compute_residual()
        residual = 0.0
        residual_company_signed = 0.0
        sign = self.type in ['in_refund', 'out_refund'] and -1 or 1
        for line in self.sudo().move_id.line_ids:
            if line.account_id.internal_type in ('receivable', 'payable'):
                residual_company_signed += line.amount_residual
                if line.currency_id == self.currency_id:
                    residual += line.amount_residual_currency if line.currency_id else line.amount_residual
                else:
                    from_currency = (line.currency_id and line.currency_id.with_context(date=line.date)) or line.company_id.currency_id.with_context(date=line.date)
                    residual += from_currency.compute(line.amount_residual, self.currency_id)

        if self.discount_total > 0:
            residual -= self.discount_total
        if self.discount_percent > 0:
            residual -= self.amount_untaxed * self.discount_percent / 100

        self.residual_company_signed = abs(residual_company_signed) * sign
        self.residual_signed = abs(residual) * sign
        self.residual = abs(residual)
        digits_rounding_precision = self.currency_id.rounding
        if float_is_zero(self.residual, precision_rounding=digits_rounding_precision):
            self.reconciled = True
        else:
            self.reconciled = False

    @api.multi
    def action_move_create(self):
        res = super(POSInvoiceTotalDisc, self).action_move_create()
        order = self.env['pos.order'].search([('invoice_id', '=', self.id)])
        session = None
        if order:
            if order.discount_total > 0 or order.discount_percent > 0:
                session = order.session_id
                discount_ac = None
                if session:
                    if session.config_id.discount_account:
                       discount_ac = session.config_id.discount_account
                    else:
                        raise UserError(_('Please set a discount account for this session'))
                lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id), ('debit', '>', 0)], limit=1)
                if order.discount_total > 0:
                    discount = order.discount_total
                elif order.discount_percent > 0:
                    move_lines = self.env['account.move.line'].search([('move_id', '=', self.move_id.id), ('credit', '>', 0)])
                    sum = 0
                    for i in move_lines:
                        sum += i.credit
                    discount = sum - order.amount_total
                lines.write({
                    'debit': lines.debit - discount
                })
                temp2 = {
                    'partner_id': self.partner_id.id,
                    'name': "Discount",
                    'credit': 0,
                    'debit': discount,
                    'account_id': discount_ac.id,
                    'quantity': 1,
                    'move_id': self.move_id.id,
                }
                self.env['account.move.line'].create(temp2)
        return res


class PosConfigNew(models.Model):
    _inherit = 'pos.config'
    # discount account is used to enter the total discount values
    discount_account = fields.Many2one('account.account', string="Discount Account", required=True)