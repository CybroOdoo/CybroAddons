# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    """Created the class for creating a new model rental order contract"""
    _name = "rental.order.contract"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Rental Order Contract'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference', copy=False,
                               readonly=True, default=lambda self: _('New'),
                               help='Create a reference number for rental contract')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='To set the customer for the contract')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain="[('rental', '=', True)]",
                                 help='To add the rental product')
    qty = fields.Float(string='Quantity', help='To add the quantity')
    currency_id = fields.Many2one('res.currency', string="Currency",
                                  related='company_id.currency_id',
                                  help='To add the company currency')
    unit_price = fields.Monetary(string='Unit Price', readonly=True,
                                 help='To set the unit price')
    date_start = fields.Datetime(string='Start Date',
                                 help='To set the start date')
    date_end = fields.Datetime(string='End Date', help='To set the end date')
    sale_order_id = fields.Many2one('sale.order', string='Sale Order',
                                    help='To set the corresponding sale order')
    rental_order_id = fields.Many2one('sale.order.line', string='Rental Order',
                                      help='To set the corresponding rental order',
                                      domain=[('is_rental', '=', True)])
    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company,
                                 string='Company',
                                 help='To set the default company')
    contract_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'), ('expired', 'Expired'),
         ('cancel', 'Cancelled')], string='Contract Status',
        default='new', help='To add contract status')

    @api.onchange('date_start', 'date_end')
    def _onchange_date_start(self):
        """Checking the end date is less than start date"""
        if self.date_start and self.date_end and self.date_start > self.date_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))

    @api.model
    def create(self, vals):
        """Creating sequence for the rental contract"""
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'rental.order.contract') or _('New')

        return super(RentalOrderContract, self).create(vals)

    def action_confirm_contract(self):
        """ Function for confirming the contract """
        self.contract_status = 'confirmed'

    def action_reset_contract(self):
        """Function for reset the contract to draft"""
        self.contract_status = 'new'

    def action_cancel_contract(self):
        """ Function for cancel contract """
        self.contract_status = 'cancel'

    def _contract_expiration(self):
        """Calculating the expiration date of the contract"""
        rental_contract = self.env['rental.order.contract'].search(
            [('contract_status', 'not in', ['expired', 'cancel'])])
        for rec in rental_contract:
            if rec.date_end and rec.date_end.date() < fields.date.today():
                rec.contract_status = 'expired'
