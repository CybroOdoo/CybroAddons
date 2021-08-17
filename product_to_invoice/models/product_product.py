# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2021-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Midilaj V K (<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import models, fields, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _compute_add_to_invoice(self):
        context = self.env.context
        for rec in self:
            if context.get('add_to_invoice'):
                rec.add_to_invoice = True
            else:
                rec.add_to_invoice = False

    add_to_invoice = fields.Boolean(compute=_compute_add_to_invoice, help='To show add to invoice button in tree view')

    def _get_invoice_taxes(self, move_id, account_id):
        """
        return taxes of selected product
        :param move_id:
        :param account_id:
        :return:
        """
        self.ensure_one()
        if move_id.move_type == 'out_invoice':
            # Out invoice.
            if self.taxes_id:
                tax_ids = self.taxes_id.filtered(lambda tax: tax.company_id == move_id.company_id)
            elif account_id.tax_ids:
                tax_ids = account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids:
                tax_ids = move_id.company_id.account_sale_tax_id
        elif move_id.move_type == 'in_invoice':
            # In invoice.
            if self.supplier_taxes_id:
                tax_ids = self.supplier_taxes_id.filtered(lambda tax: tax.company_id == move_id.company_id)
            elif account_id.tax_ids:
                tax_ids = account_id.tax_ids
            else:
                tax_ids = self.env['account.tax']
            if not tax_ids:
                tax_ids = move_id.company_id.account_purchase_tax_id
        else:
            tax_ids = account_id.tax_ids

        if self.company_id and tax_ids:
            tax_ids = tax_ids.filtered(lambda tax: tax.company_id == self.company_id)

        return tax_ids

    def _get_invoice_account(self, move_id):
        """
        return income/expense account of selected product
        :param move_id:
        :return:
        """
        self.ensure_one()
        self = self.with_company(move_id.journal_id.company_id)

        fiscal_position = move_id.fiscal_position_id
        accounts = self.product_tmpl_id.get_product_accounts(fiscal_pos=fiscal_position)
        if move_id.move_type == 'out_invoice':
            # Out invoice.
            return accounts['income']
        elif move_id.move_type == 'in_invoice':
            # In invoice.
            return accounts['expense']

    def action_add_to_invoice(self):
        active_id = self._context.get('active_id')
        invoice_id = self.env['account.move'].browse(active_id)
        account_id = self._get_invoice_account(invoice_id)
        tax_ids = self._get_invoice_taxes(invoice_id, account_id)
        invoice_id.write({
            'invoice_line_ids': [(0, 0, {
                'product_id': self.id,
                'product_uom_id': self.uom_id.id,
                'quantity': 1,
                'price_unit': self.lst_price if invoice_id.move_type == 'out_invoice' else self.standard_price,
                'account_id': account_id,
                'tax_ids': tax_ids
            })]
        })

    def action_change_qty(self):
        active_id = self._context.get('active_id')
        invoice_id = self.env['account.move'].browse(active_id)
        return {
            'name': _('Product Details'),
            'type': 'ir.actions.act_window',
            'res_model': 'invoice.product.details.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_account_move_id': invoice_id.id,
                'default_product_id': self.id,
                'default_price_unit': self.lst_price if invoice_id.move_type == 'out_invoice' else self.standard_price,
            },
        }
