from openerp import api, models, fields
from openerp.osv import osv
import openerp.addons.decimal_precision as dp


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    discount = fields.Float(string='Discount (%)',
                            digits=(16, 10),
                            # digits= dp.get_precision('Discount'),
                            default=0.0)

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        disc = 0.0
        for inv in self:
            for line in inv.invoice_line:
                print line.discount
                disc += (line.quantity * line.price_unit) * line.discount / 100
        self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
        self.amount_tax = sum(line.amount for line in self.tax_line)
        self.amount_discount = disc
        self.amount_total = self.amount_untaxed + self.amount_tax

    discount_type = fields.Selection([('percent', 'Percentage'), ('amount', 'Amount')], 'Discount Type', readonly=True,
                                     states={'draft': [('readonly', False)]})
    discount_rate = fields.Float('Discount Rate',
                                 digits_compute=dp.get_precision('Account'),
                                 readonly=True,
                                 states={'draft': [('readonly', False)]})
    amount_discount = fields.Float(string='Discount',
                                   digits=dp.get_precision('Account'),
                                   readonly=True, compute='_compute_amount')
    amount_untaxed = fields.Float(string='Subtotal', digits=dp.get_precision('Account'),
                                  readonly=True, compute='_compute_amount', track_visibility='always')
    amount_tax = fields.Float(string='Tax', digits=dp.get_precision('Account'),
                              readonly=True, compute='_compute_amount')
    amount_total = fields.Float(string='Total', digits=dp.get_precision('Account'),
                                readonly=True, compute='_compute_amount')

    @api.multi
    def compute_discount(self, discount):
        for inv in self:
            val1 = val2 = 0.0
            disc_amnt = 0.0
            val2 = sum(line.amount for line in self.tax_line)
            for line in inv.invoice_line:
                val1 += (line.quantity * line.price_unit)
                line.discount = discount
                disc_amnt += (line.quantity * line.price_unit) * discount / 100
            total = val1 + val2 - disc_amnt
            self.amount_discount = disc_amnt
            self.amount_tax = val2
            self.amount_total = total

    @api.onchange('discount_type', 'discount_rate')
    def supply_rate(self):
        for inv in self:
            if inv.discount_rate != 0:
                amount = sum(line.price_subtotal for line in self.invoice_line)
                tax = sum(line.amount for line in self.tax_line)
                if inv.discount_type == 'percent':
                    self.compute_discount(inv.discount_rate)
                else:
                    total = 0.0
                    discount = 0.0
                    for line in inv.invoice_line:
                        total += (line.quantity * line.price_unit)
                    if inv.discount_rate != 0:
                        discount = (inv.discount_rate / total) * 100
                    self.compute_discount(discount)

    @api.model
    def _prepare_refund(self, invoice, date=None, period_id=None, description=None, journal_id=None):
        res = super(AccountInvoice, self)._prepare_refund(invoice, date, period_id,
                                                          description, journal_id)
        res.update({
            'discount_type': self.discount_type,
            'discount_rate': self.discount_rate,
        })
        return res

