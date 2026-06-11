# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SellerPayment(models.Model):
    """ Managing seller payments"""
    _name = 'seller.payment'
    _description = "Seller Payment"

    name = fields.Char(string='Record Reference', required=True,
                       help="Sequence of the payment", readonly=True,
                       default='New')
    seller_id = fields.Many2one(
        'res.partner', string='Seller',
        required=True,
        default=lambda self: self.env.user.partner_id.id,
        help="Seller details")
    payment_mode = fields.Selection(
        selection=[('Cash', 'Cash'),
                   ('Bank', 'Bank')],
        string="Payment Mode",
        help="To select the mode of payment",
        required=True, default='Cash')
    memo = fields.Char(string='Memo', help="Description", required=True)
    payable_amount = fields.Float(string='Payable Amount', help="Total amount",
                                  required=True)
    date = fields.Date(string='Payment Date', required=True,
                       help="Date of the payment", default=fields.Date.today)
    type_id = fields.Many2one('account.payment.method',
                              string='Type', help="Payment method",
                              required=True)
    invoice_cashable = fields.Boolean(string='Invoice Cashable',
                                      help="Total amount that to invoice")
    description = fields.Text(string='Description', help="Description")
    commission = fields.Float(string="Commission",
                              help="Total commission amount")
    state = fields.Selection(selection=[('Draft', 'Draft'),
                                        ('Requested', 'Requested'),
                                        ('Validated', 'Validated'),
                                        ('Rejected', 'Rejected'),
                                        ('cancelled', 'Cancelled')],
                             string="state",
                             help="State of the seller payment",
                             default="Draft")

    def request(self):
        """ Request for payment and check payment term settings values  """
        self.state = 'Requested'
        amount_limit = self.env['ir.config_parameter'].sudo().get_param(
            'multi_vendor_marketplace.amt_limit')
        min_gap = self.env['ir.config_parameter'].sudo().get_param(
            'multi_vendor_marketplace.min_gap')
        partner_id = self.env['res.partner'].search(
            [('id', '=', self.seller_id.id)])
        today_date = fields.Date.today()
        mingap_date = fields.Date.subtract(today_date, days=int(min_gap))
        date_info_record = self.env['seller.payment'].search(
            [('seller_id', '=', self.seller_id.id),
             ('state', '=', 'Validated'), ('date', '>=', mingap_date)],
            order='date DESC')
        for checkdate in date_info_record:
            if (self.payable_amount > partner_id.total_commission
                    or self.payable_amount > int(
                    amount_limit) or checkdate.date >= mingap_date):
                raise ValidationError(
                    _("Entered amount is greater than your commission or "
                      "Amount limit is " + amount_limit + " and Minimum gap "
                        "for next payment request " + min_gap + " days"))
            break

    def reject(self):
        """ Payment request will reject """
        self.state = 'Rejected'

    def cancel(self):
        """ Payment request will cancel """
        self.state = 'cancelled'

    def validate(self):
        """ Payment request will validte and substarct that amount
        from commission """
        self.state = 'Validated'
        config_parameter = self.env['ir.config_parameter'].sudo()
        partner_id = self.seller_id
        if self.payable_amount > partner_id.total_commission:
            raise ValidationError(
                _("Entered amount is greater than the total commission earned."))

        product_config = config_parameter.get_param(
            'multi_vendor_marketplace.pay_product')
        if not product_config:
            raise ValidationError(_("Payment product is not configured in settings."))
        product = self.env['product.product'].browse(int(product_config))

        currency_config = config_parameter.get_param(
            'multi_vendor_marketplace.currency')
        currency_id = int(currency_config) if currency_config else self.env.company.currency_id.id

        journal_config = config_parameter.get_param(
            'multi_vendor_marketplace.pay_journal')
        if not journal_config:
            raise ValidationError(_("Payment journal is not configured in settings."))
        journal_id = int(journal_config)

        # Get the account from the product or category
        account_id = product.property_account_expense_id or product.categ_id.property_account_expense_categ_id
        if not account_id:
            # Fallback to the journal's default account if possible or raise error
            account_id = self.env['account.journal'].browse(journal_id).default_account_id
            if not account_id:
                raise ValidationError(_("Please configure an expense account for the payment product or set a default account on the payment journal."))

        self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.seller_id.id,
            'ref': self.seller_id.profile_url or self.name,
            'invoice_date': self.date,
            'currency_id': currency_id,
            'journal_id': journal_id,
            'invoice_line_ids':
                [(0, 0,
                  {
                      'product_id': product.id,
                      'name': self.memo,
                      'account_id': account_id.id,
                      'quantity': 1,
                      'price_unit': self.payable_amount,
                      'tax_ids': False,
                  })]
        })
        partner_id.total_commission = partner_id.total_commission - self.payable_amount

    @api.onchange('seller_id')
    def onchange_seller(self):
        """ For getting default commission"""
        partner_id = self.seller_id
        self.commission = partner_id.total_commission

    @api.model
    def create(self, vals):
        """ For getting the sequence number"""
        if vals.get('name', 'New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'seller.payment')
        res = super(SellerPayment, self).create(vals)
        return res
