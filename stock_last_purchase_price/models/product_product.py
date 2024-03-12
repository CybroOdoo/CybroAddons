# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero


class ProductProduct(models.Model):
    """ Class to inherit product_product to add some functionalities """
    _inherit = 'product.product'

    def create_price_change_account_move(self, new_price, account_id,
                                         company_id, origin):
        """ Function to compute and updated the change in price """
        account_move = self.env['account.move']
        product_accounts = {
            product.id: product.product_tmpl_id.get_product_accounts() for
            product in self}
        for product in self.with_context().filtered(
                lambda r: r.valuation == 'real_time'):
            diff = product.standard_price - new_price
            if not float_is_zero(
                    diff, precision_rounding=product.currency_id.rounding):
                if not product_accounts[product.id].get('stock_valuation',
                                                        False):
                    raise UserError(
                        _('You don\'t have any stock valuation account '
                          'defined on your product category. You must define '
                          'one before processing this operation.'))
                qty_available = product.qty_available
                if qty_available:
                    # Accounting Entries
                    if diff * qty_available > 0:
                        debit_account_id = account_id
                        credit_account_id = product_accounts[product.id][
                            'stock_valuation'].id
                    else:
                        debit_account_id = product_accounts[product.id][
                            'stock_valuation'].id
                        credit_account_id = account_id
                    move_vals = {
                        'journal_id': product_accounts[product.id][
                            'stock_journal'].id,
                        'company_id': company_id,
                        'ref': product.default_code,
                        'line_ids': [(0, 0, {
                            'name': _('%s changed cost from %s to %s - %s') % (
                                origin, product.standard_price, new_price,
                                product.display_name),
                            'account_id': debit_account_id,
                            'debit': abs(diff * qty_available),
                            'credit': 0,
                            'product_id': product.id,
                        }), (0, 0, {
                            'name': _('%s changed cost from %s to %s - %s') % (
                                origin, product.standard_price, new_price,
                                product.display_name),
                            'account_id': credit_account_id,
                            'debit': 0,
                            'credit': abs(diff * qty_available),
                            'product_id': product.id,
                        })],
                    }
                    move = account_move.create(move_vals)
                    move.action_post()
        return True

    @api.depends('stock_move_ids.product_qty', 'stock_move_ids.state',
                 'stock_move_ids.remaining_value',
                 'product_tmpl_id.cost_method',
                 'product_tmpl_id.standard_price',
                 'product_tmpl_id.property_valuation',
                 'product_tmpl_id.categ_id.property_valuation')
    def _compute_stock_value(self):
        """ Function to compute the stock moves and update the values """
        stock_move = self.env['stock.move']
        to_date = self.env.context.get('to_date')
        self.env['account.move.line'].check_access_rights('read')
        fifo_automated_values = {}
        query = """SELECT aml.product_id, aml.account_id, 
                sum(aml.debit) - sum(aml.credit), sum(quantity), 
                array_agg(aml.id) FROM account_move_line AS aml
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
            fifo_automated_values[(row[0], row[1])] = (
             row[2], row[3], list(row[4]))
        for product in self:
            if product.cost_method in ['standard', 'average', 'last']:
                qty_available = product.with_context(
                    company_owned=True, owner_id=False).qty_available
                price_used = product.standard_price
                if to_date:
                    price_used = product.get_history_price(
                        self.env.user.company_id.id, date=to_date)
                product.stock_value = price_used * qty_available
                product.qty_at_date = qty_available
            elif product.cost_method == 'fifo':
                if to_date:
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        domain = [('product_id', '=', product.id),
                                  ('date', '<=',
                                   to_date)] + stock_move._get_all_base_domain()
                        moves = stock_move.search(domain)
                        product.stock_value = sum(moves.mapped('value'))
                        product.qty_at_date = product.with_context(
                            company_owned=True, owner_id=False).qty_available
                        product.stock_fifo_manual_move_ids = stock_move.browse(
                            moves.ids)
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get(
                            (product.id, valuation_account_id)) or (
                                                       0, 0, [])
                        product.stock_value = value
                        product.qty_at_date = quantity
                        product.stock_fifo_real_time_aml_ids = self.env[
                            'account.move.line'].browse(aml_ids)
                else:
                    product.stock_value, moves = product._sum_remaining_values()
                    product.qty_at_date = product.with_context(
                        company_owned=True, owner_id=False).qty_available
                    if product.product_tmpl_id.valuation == 'manual_periodic':
                        product.stock_fifo_manual_move_ids = moves
                    elif product.product_tmpl_id.valuation == 'real_time':
                        valuation_account_id = product.categ_id.property_stock_valuation_account_id.id
                        value, quantity, aml_ids = fifo_automated_values.get(
                            (product.id, valuation_account_id)) or (
                                                       0, 0, [])
                        product.stock_fifo_real_time_aml_ids = self.env[
                            'account.move.line'].browse(aml_ids)
