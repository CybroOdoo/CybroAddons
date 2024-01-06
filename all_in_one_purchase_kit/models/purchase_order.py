# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Mohamed Muzammil VP (odoo@cybrosys.com)
#
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
###############################################################################
import datetime
import calendar
from odoo import api, fields, models


class PurchaseOrder(models.Model):
    """ Inherit purchase.order model and add fields and methods """
    _inherit = 'purchase.order'

    requisition_order = fields.Char(
        string='Requisition Order', help='Requisition Order'
    )
    company_currency_amount = fields.Float(
        string='Company Currency Total', compute='_compute_amount',
        help="Total amount in company currency"
    )
    number_to_words = fields.Char(
        string="Amount in Words (Total) : ",
        compute='_compute_number_to_words', help="Total amount in words"
    )

    def _compute_amount(self):
        """Total amount in company currency"""
        for amount in self:
            amount.company_currency_amount = self.env['res.currency']._compute(
                amount.currency_id, amount.company_id.currency_id,
                amount.amount_total)

    def _compute_number_to_words(self):
        """Compute the amount to words in Purchase Order"""
        for rec in self:
            rec.number_to_words = rec.currency_id.amount_to_text(
                rec.amount_total)

    def action_multi_confirm(self):
        """Confirm multiple order by a single click"""
        for order in self.env['purchase.order'].browse(
                self.env.context.get('active_ids')).filtered(
            lambda o: o.state in ['draft', 'sent']):
            order.button_confirm()

    def action_multi_cancel(self):
        """Cancel multiple order by a single click"""
        for order in self.env['purchase.order'].browse(
                self.env.context.get('active_ids')):
            order.button_cancel()

    def button_confirm(self):
        """The same order line merges when the confirmation button is
         clicked"""
        line_groups = {}
        for line in self.order_line:
            key = (line.product_id.id, line.price_unit)
            line_groups.setdefault(key, []).append(line)
        for lines in line_groups.values():
            if len(lines) > 1:
                lines[0].product_qty = sum(line.product_qty for line in lines)
                lines[0]._compute_amount()
                for line in lines[1:]:
                    line.unlink()
        res = super(PurchaseOrder, self).button_confirm()
        return res

    @api.onchange('partner_id')
    def _recompute_discount(self):
        """Calculate the discount"""
        self.order_line.calculate_discount_percentage()

    @api.model
    def get_data(self):
        """Get various counts and total amounts related to different states
         of purchase-related records."""
        return{
            'rfq': self.search_count([('state', '=', 'draft')]),
            'rfq_sent': self.search_count([('state', '=', 'sent')]),
            'rfq_to_approve': self.search_count([('state', '=', 'to approve')]),
            'purchase_order': self.search_count([('state', '=', 'purchase')]),
            'cancelled_order': self.search_count([('state', '=', 'cancel')]),
            'amount_total': sum(self.search([
                ('state', '=', 'purchase')]).mapped('amount_total')),
            'amount_rfq': sum(self.search([
                ('state', '=', 'draft')]).mapped('amount_total')),
        }

    @api.model
    def get_value(self, start_date, end_date):
        """It is to pass values according to start and end date to the
        dashboard."""
        if start_date and end_date:
            rfq = self.search_count(
                [('state', '=', 'draft'), ('date_order', '>=', start_date),
                 ('date_order', '<=', end_date)])
            rfq_sent = self.search_count(
                [('state', '=', 'sent'), ('date_order', '>=', start_date),
                 ('date_order', '<=', end_date)])
            rfq_to_approve = self.search_count(
                [('state', '=', 'to approve'),
                 ('date_order', '>=', start_date),
                 ('date_order', '<=', end_date)])
            purchase_order = self.search_count(
                [('state', '=', 'purchase'), ('date_order', '>=', start_date),
                 ('date_order', '<=', end_date)])
            cancelled_order = self.search_count(
                [('state', '=', 'cancel'), ('date_order', '>=', start_date),
                 ('date_order', '<=', end_date)])
            amount_total = sum(self.search([
                ('state', '=', 'purchase'), ('date_order', '>=', start_date),
                ('date_order', '<=', end_date)]).mapped('amount_total'))
            amount_rfq = sum(self.search([
                ('state', '=', 'draft'), ('date_order', '>=', start_date),
                ('date_order', '<=', end_date)]).mapped('amount_total'))
        elif start_date:
            rfq = self.search_count([('state', '=', 'draft'),
                                     ('date_order', '>=', start_date)])
            rfq_sent = self.search_count([('state', '=', 'sent'),
                                          ('date_order', '>=', start_date)])
            rfq_to_approve = self.search_count(
                [('state', '=', 'to approve'),
                 ('date_order', '>=', start_date),
                 ])
            purchase_order = self.search_count(
                [('state', '=', 'purchase'), ('date_order', '>=', start_date)])
            cancelled_order = self.search_count(
                [('state', '=', 'cancel'), ('date_order', '>=', start_date)])
            amount_total = sum(self.search([
                ('state', '=', 'purchase'), ('date_order', '>=', start_date)
            ]).mapped('amount_total'))
            amount_rfq = sum(self.search([
                ('state', '=', 'draft'), ('date_order', '>=', start_date)
            ]).mapped('amount_total'))
        elif end_date:
            rfq = self.search_count(
                [('state', '=', 'draft'), ('date_order', '<=', end_date)])
            rfq_sent = self.search_count(
                [('state', '=', 'sent'),
                 ('date_order', '<=', end_date)])
            rfq_to_approve = self.search_count(
                [('state', '=', 'to approve'),
                 ('date_order', '<=', end_date),
                 ])
            purchase_order = self.search_count(
                [('state', '=', 'purchase'), ('date_order', '<=', end_date)])
            cancelled_order = self.search_count(
                [('state', '=', 'cancel'), ('date_order', '<=', end_date)])
            amount_total = sum(self.search([
                ('state', '=', 'purchase'), ('date_order', '<=', end_date)
            ]).mapped('amount_total'))
            amount_rfq = sum(self.search([
                ('state', '=', 'draft'), ('date_order', '>=', start_date)
            ]).mapped('amount_total'))
        return {
            'rfq': rfq,
            'rfq_sent': rfq_sent,
            'rfq_to_approve': rfq_to_approve,
            'purchase_order': purchase_order,
            'cancelled_order': cancelled_order,
            'amount_total': amount_total,
            'amount_rfq': amount_rfq,
        }

    @api.model
    def get_current_month_purchase(self):
        """Returns current month purchase"""
        date = fields.Datetime.today()
        start_date = datetime.datetime(date.year, date.month, 1)
        purchase_order = self.search_count(
            [('create_date', '<', date), ('create_date', '>', start_date),
             ('state', '=', 'purchase')]
        )
        current_month_count = {
            calendar.month_name[date.month]: purchase_order
        }
        return{
            'current_month_count': current_month_count
        }

    @api.model
    def get_monthly_purchase_order(self):
        """Returns monthly purchase count data to the graph of dashboard"""
        monthly_purchase = {}
        purchase_order = self.search([('state', '=', 'purchase')])
        lst = [rec.create_date.month for rec in purchase_order]
        for i in range(1, 13):
            count = lst.count(i)
            monthly_purchase.update({
                calendar.month_name[i]: count
            })
        return {
            'monthly_purchase_count': monthly_purchase,
        }

    @api.model
    def get_monthly_order(self):
        """Returns complete monthly data includes rfq, purchase order,
        canceled order,to approve order etc. of to the graph of dashboard"""
        monthly_count = {}
        purchase_order = self.search([])
        lst = [rec.create_date.month for rec in purchase_order]
        for i in range(1, 13):
            count = lst.count(i)
            monthly_count.update({
                calendar.month_name[i]: count
            })
        return {
            'monthly_count': monthly_count,
        }

    @api.model
    def total_amount_spend(self):
        """Returns total amount spend for purchase"""
        total_amount = sum(self.search([
            ('state', '=', 'purchase')]).mapped('amount_total'))
        return {
            'amount_total': total_amount
        }

    def recommendation_wizard(self):
        """Add data to wizard"""
        orders = self.search([('partner_id', '=', self.partner_id.id)])
        pro_id = []
        for order in orders:
            for product in order.order_line.product_id:
                val = (0, 0, {
                    'product_id': product.id,
                    'available_qty': product.qty_available,
                    'list_price': product.list_price,
                    'qty_need': 0,
                    'is_modified': False,
                })
                if val not in pro_id:
                    pro_id.append(val)
            res = {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'product.recommendation',
                'target': 'new',
                'context': {
                    'default_line_ids': pro_id,
                }
            }
        return res
