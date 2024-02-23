# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aswathi PN (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RentalOrderContract(models.Model):
    """Model for showing the rental order contracts"""
    _name = "rental.order.contract"
    _description = 'Rental Order Contract'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference', copy=False,
                               readonly=True, default=lambda self: _('New'),
                               help='To store the reference number to the '
                                    'rental contract')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='To add the customer of the rental order')
    product_id = fields.Many2one('product.product', string='Rental Product',
                                 help='To add the rental product')
    qty = fields.Float(string='Quantity',
                       help='To add the rental product quantity')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  help='To add the company currency')
    unit_price = fields.Monetary(string='Unit Price',
                                 help='To add the unit price of the product')
    date_start = fields.Datetime(string='Start Date',
                                 help='Contract start date')
    date_end = fields.Datetime(string='End Date', help='Contract end date')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order',
                                    help='Sale of the contract')
    rental_order_id = fields.Many2one('sale.order.line', string='Rental Order',
                                      help='Rental order of the contract')
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 help='Set the company')
    contract_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'), ('expired', 'Expired'),
         ('cancel', 'Cancelled')],
        default='new', string='Contract Status',
        help='To show the contract status')

    @api.onchange('date_start', 'date_end')
    def _onchange_date_start(self):
        """Checking whether the end date is less than or equal to the start date"""
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))

    def _contract_expiration(self):
        """Calculating the expiration date of the contract"""
        rental_contract = self.env['rental.order.contract'].search(
            [('contract_status', 'not in', ['expired', 'cancel'])])
        for rec in rental_contract:
            if rec.date_end:
                if rec.date_end.date() < fields.date.today():
                    rec.contract_status = 'expired'

    def action_confirm_contract(self):
        """ Function for contract confirmation"""
        self.contract_status = 'confirmed'

    def action_cancel_contract(self):
        """ Function for cancel contract"""
        self.contract_status = 'cancel'

    @api.model
    def create(self, vals):
        """Creating sequence for the rental contract"""
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'rental.order.contract') or _('New')
        return super(RentalOrderContract, self).create(vals)
