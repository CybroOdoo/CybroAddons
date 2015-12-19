from openerp import api, models, fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_tax = sum(line.amount for line in self.tax_line)
        if self.discount_type == 'percent':
            self.amount_discount = ((self.amount_untaxed + self.amount_tax) * self.discount_rate) / 100
        elif self.discount_type == 'amount':
            self.amount_discount = self.discount_rate
        self.amount_total = self.amount_untaxed + self.amount_tax - self.amount_discount

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type', readonly=True,
                                     states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount rate', digits_compute=dp.get_precision('Account'), readonly=True,
                                 states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount', digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount')
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
                                  readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'),
                              readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                readonly=True, compute='_compute_amount')

    @api.onchange('discount_type', 'discount_rate')
    def compute_discount(self):
        for inv in self:
            amount = sum(line.price_subtotal for line in self.invoice_line)
            tax = sum(line.amount for line in self.tax_line)
            if inv.discount_type == 'percent':
                if inv.discount_rate == 100:
                    disc_amnt = amount + tax
                else:
                    disc_amnt = (amount + tax) * inv.discount_rate / 100
                total = amount + tax - disc_amnt
                self.amount_discount = disc_amnt
                self.amount_total = total
            else:
                total = (amount + tax) - inv.discount_rate
                self.amount_discount = inv.discount_rate
                self.amount_total = total

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date, period_id,
                                                          description, journal_id)
        res.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return res


class invoice_line(osv.Model):
    _inherit = 'account.invoice.line'

    def move_line_get(self, cr, uid, invoice_id, context=None):
        res = super(invoice_line, self).move_line_get(cr, uid, invoice_id, context=context)
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)

        if inv.type in ('out_invoice', 'out_refund') and inv.discount_type:
            prop = self.pool.get('ir.property').get(cr, uid, 'property_account_income_categ', 'product.category',
                                                    context=context)
            prop_id = prop and prop.id or False
            account_id = self.pool.get('account.fiscal.position').map_account(cr, uid, inv.fiscal_position or False,
                                                                              prop_id)
            sign = -1

            res.append({
                'name': 'Discount',
                'price_unit': sign * inv.amount_discount,
                'quantity': 1,
                'price': sign * inv.amount_discount,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })
        return res
