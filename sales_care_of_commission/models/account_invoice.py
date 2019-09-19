# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Akhilesh N S (odoo@cybrosys.com)
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
#############################################################################

from odoo import models, fields, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    care_of_partner_id = fields.Many2one('res.partner', string='Care Of (C/O)', required=False,
                                         readonly=True,
                                         states={'draft': [('readonly', False)]},
                                         help="To address a contact in care of someone else")
    care_of_percentage = fields.Float(string='C/O Commission Percentage', readonly=True,
                                      states={'draft': [('readonly', False)]})
    care_of_commission = fields.Monetary(string='C/O Commission Amount',
                                         store=True, readonly=True, compute='_compute_amount')

    @api.onchange('partner_id', 'company_id')
    def _onchange_partner_id(self):
        res = super(AccountInvoice, self)._onchange_partner_id()
        self.care_of_partner_id = self.partner_id.care_of_partner_id
        self.care_of_percentage = self.partner_id.care_of_percentage
        return res

    @api.one
    @api.depends('invoice_line_ids.price_subtotal', 'tax_line_ids.amount', 'tax_line_ids.amount_rounding',
                 'currency_id', 'company_id', 'date_invoice', 'type')
    def _compute_amount(self):
        """Compute C/O Commission Amount"""
        res = super(AccountInvoice, self)._compute_amount()
        self.care_of_commission = self.amount_untaxed * self.care_of_percentage
        return res
    
    @api.model
    def create(self, vals):
        """Adding c/o data from sale order to invoice. Commission amount not passing, it will
        compute from invoice model"""
        if vals.get('origin'):
            order_id = self.env['sale.order'].search([('name', '=', vals.get('origin'))])
            vals.update(dict(care_of_partner_id=order_id.care_of_partner_id.id or False,
                             care_of_percentage=order_id.care_of_percentage
                             ))
        return super(AccountInvoice, self).create(vals)
