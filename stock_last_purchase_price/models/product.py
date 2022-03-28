# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('last', 'Last Purchase Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string='Costing Method',
        company_dependent=True, copy=True,
        help="""Standard Price: The products are valued at their standard cost defined on the product.
            Average Cost (AVCO): The products are valued at weighted average cost.
            First In First Out (FIFO): The products are valued supposing those that enter the company first will also leave it first.
            Last Purchase Price: The products are valued same as 'Standard Price' Method, But standard price defined on the product will updated automatically with last purchase price.""")


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    property_cost_method = fields.Selection([
        ('standard', 'Standard Price'),
        ('last', 'Last Purchase Price'),
        ('fifo', 'First In First Out (FIFO)'),
        ('average', 'Average Cost (AVCO)')], string='Costing Method',
        company_dependent=True, copy=True,
        help="""Standard Price: The products are valued at their standard cost defined on the product.
        Average Cost (AVCO): The products are valued at weighted average cost.
        First In First Out (FIFO): The products are valued supposing those that enter the company first will also leave it first.
        Last Purchase Price: The products are valued same as 'Standard Price' Method, But standard price defined on the product will be updated automatically with last purchase price.""")

    
    def _set_cost_method(self):
        # When going from FIFO to AVCO or to standard, we update the standard price with the
        # average value in stock.
        if self.property_cost_method == 'fifo' and self.cost_method in ['average', 'standard', 'last']:
            # Cannot use the `stock_value` computed field as it's already invalidated when
            # entering this method.
            valuation = sum([variant._sum_remaining_values()[0] for variant in self.product_variant_ids])
            qty_available = self.with_context(company_owned=True).qty_available
            if qty_available:
                self.standard_price = valuation / qty_available
        return self.write({'property_cost_method': self.cost_method})


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def create_price_change_account_move(self, new_price, account_id, company_id, origin):
        """
            """
        AccountMove = self.env['account.move']
        product_accounts = {product.id: product.product_tmpl_id.get_product_accounts() for product in self}
        for product in self.with_context().filtered(lambda r: r.valuation == 'real_time'):
            diff = product.standard_price - new_price
            if not float_is_zero(diff, precision_rounding=product.currency_id.rounding):
                if not product_accounts[product.id].get('stock_valuation', False):
                    raise UserError(_('You don\'t have any stock valuation account defined on your product category. You must define one before processing this operation.'))
                qty_available = product.qty_available
                if qty_available:
                    # Accounting Entries
                    if diff * qty_available > 0:
                        debit_account_id = account_id
                        credit_account_id = product_accounts[product.id]['stock_valuation'].id
                    else:
                        debit_account_id = product_accounts[product.id]['stock_valuation'].id
                        credit_account_id = account_id

                    move_vals = {
                        'journal_id': product_accounts[product.id]['stock_journal'].id,
                        'company_id': company_id,
                        'ref': product.default_code,
                        'line_ids': [(0, 0, {
                            'name': _('%s changed cost from %s to %s - %s') % (origin, product.standard_price, new_price, product.display_name),
                            'account_id': debit_account_id,
                            'debit': abs(diff * qty_available),
                            'credit': 0,
                            'product_id': product.id,
                        }), (0, 0, {
                            'name': _('%s changed cost from %s to %s - %s') % (origin, product.standard_price, new_price, product.display_name),
                            'account_id': credit_account_id,
                            'debit': 0,
                            'credit': abs(diff * qty_available),
                            'product_id': product.id,
                        })],
                    }
                    move = AccountMove.create(move_vals)
                    move.post()
        return True


    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state', 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method', 'product_tmpl_id.standard_price', 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        StockMove = self.env['stock.move']
        to_date = self.env.context.get('to_date')

        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, sum(aml.debit) - sum(aml.credit), sum(quantity), array_agg(aml.id)
                         FROM account_move_line AS aml
                        WHERE aml.product_id IS NOT NULL AND aml.company_id=%%s %s
                     GROUP BY aml.product_id, aml.account_id"""
        params = (self.env.user.company_id.id,)
        if to_date:
            query = query % ('AND aml.date <= %s',)
            params = params + (to_date,)
        else:
            query = query % ('',)
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        for row in res:
            fifo_automated_values[(row[0], row[1])] = (row[2], row[3], list(row[4]))

        for product in self:
            if product.cost_method in ['standard', 'average', 'last']:
                qty_available = product.with_context(company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id,
                        date=to_date,
                    )
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        domain = [('product_id', '=', product.id),
                                  ('date', '<=', to_date)] + StockMove._get_all_base_domain()
                        moves = StockMove.search(domain)
                        product.stock_value = sum(moves.mapped('value'))
                        product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = StockMove.browse(moves.ids)
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
                else:
                    product.stock_value, moves = product._sum_remaining_values()
                    product.qty_at_date = product.with_context(company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = moves
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get((product.id, valuation_account_id)) or (
                        0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env['account.move.line'].browse(aml_ids)
