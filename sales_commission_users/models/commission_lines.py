# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu KP (<https://www.cybrosys.com>)
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
from datetime import datetime
from odoo import fields, models, _
from odoo.exceptions import UserError


class CommissionLines(models.Model):
    """Creating a commission lines model."""
    _name = "commission.lines"
    _description = "Commission Lines"

    date = fields.Date(string="Date", help="Date")
    sale_order_id = fields.Many2one('sale.order', help="Sale order",
                                    string='Sale Order')
    description = fields.Char(string="Name", help="Description")
    sales_person_id = fields.Many2one('res.users',
                                      string='Sales Person',
                                      help="Sales person")
    order_ref = fields.Char(string='Order Reference', help="Order reference")
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help="Partner")
    commission = fields.Char(string='Commission Name',
                             help="Name of the commission")
    commission_type = fields.Selection(
        string="Commission Type",
        selection=[('standard', 'Standard'),
                   ('partner_based', 'Partner Based'),
                   ('product_based', 'Product Based'),
                   ('discount_based', 'Discount Based')
                   ], help="Commission type")
    commission_amount = fields.Float(string="Commission Amount",
                                     help="Commission Amount")

    def action_create_invoice(self):
        """Creating invoice for sales commission"""
        if len(self.sales_person_id.mapped('partner_id')) > 1:
            raise UserError(_('Sales Person should be same.'))
        else:
            lines = [(0, 0, {
                'name': rec.description,
                'quantity': 1.0,
                'discount': 0.00,
                'price_unit': rec.commission_amount,
            }) for rec in self]
            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': self.sales_person_id.mapped('partner_id').id,
                'payment_reference': self.mapped('order_ref'),
                'invoice_date': (datetime.now()).date(),
                'invoice_line_ids': lines
            })
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'domain': [
                    ('payment_reference', '=', self.mapped('order_ref'))],
                'context': "{'create': False}"
            }
