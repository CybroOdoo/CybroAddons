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


class SaleOrder(models.Model):
    """Created the class for inheriting the model sale order"""
    _inherit = 'sale.order'

    rental_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'),
         ('expired', 'Expired'),
         ('cancel', 'Cancelled')],
        default='new', help='To show the rental status', string='Rental Status')

    def action_confirm(self):
        """For creating rental order contract at the time of confirm the sale order."""
        res = super(SaleOrder, self).action_confirm()
        for product in self.order_line:
            if product.rental:
                product.is_rental = True
                self.env['rental.order.contract'].create([{
                    'partner_id': self.partner_id.id,
                    'product_id': product.product_id.id,
                    'qty': product.product_uom_qty,
                    'unit_price': product.price_unit,
                    'rental_order_id': product.id,
                    'sale_order_id': self.id,
                }])
        return res


class SaleOrderLine(models.Model):
    """Created the class for inheriting the model sale order line"""
    _inherit = 'sale.order.line'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference', readonly=True,
                               default=lambda self: _('New'),
                               help='To create reference number for sale order line')
    initial_contract_id = fields.Many2one('rental.order.contract',
                                          string='Initial Contract',
                                          help='To add initial contract')
    initial_start = fields.Datetime(string='Start Date', related='initial_contract_id.date_start',
                                    help='To add the initial contract start date')
    initial_end = fields.Datetime(string='End Date', related='initial_contract_id.date_end',
                                  help='To add initial contract end date')
    initial_qty = fields.Float(string='Quantity', related='initial_contract_id.qty',
                               help='To add initial contract product quantity')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='To store the partner of the corresponding sale order')
    current_contract_id = fields.Many2one('rental.order.contract',
                                          string='Current Contract',
                                          help='To add the current contract')
    current_start = fields.Datetime(string='Start Date', related='current_contract_id.date_start',
                                    help='To add the current contract start date')
    current_end = fields.Datetime(string='End Date', related='current_contract_id.date_end',
                                  help='To add the current contract end date')
    current_qty = fields.Float(string='Quantity', related='current_contract_id.qty',
                               help='To add the current contract product quantity')
    last_renewal_time = fields.Datetime(string='Last Renewal Time',
                                        help='To store the last renewal time of the contract')
    is_rental = fields.Boolean(string='Rental',
                               help='To check the sale order line contains rental product or not')
    rental = fields.Boolean(string='Rental', related='product_id.rental',
                            help='To check the sale order line product is rental product')
    current_contract_values = fields.Boolean(string='Contract Value',
                                             compute='_compute_current_contract_values',
                                             help='To compute the contract values')
    rental_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'),
         ('cancel', 'Cancelled')],
        default='new', help='To show the rental status', string='Rental Status')
    rental_contract_ids = fields.One2many('rental.order.contract',
                                          'rental_order_id',
                                          string='Rental Contract',
                                          help='To Shows the rental contract')

    @api.depends('rental_contract_ids')
    def _compute_current_contract_values(self):
        """For fetching the current contract values to the sale order line form view"""
        for rec in self:
            rec.current_contract_values = False
            try:
                recs_sorted = \
                    rec.rental_contract_ids.sorted(key=lambda r: r.date_start)[0] if rec.rental_contract_ids.sorted(
                        key=lambda r: r.date_start) else False
                rec.current_contract_values = True
                for record in rec.rental_contract_ids:
                    if record.date_start and record.date_end:
                        if record.date_start.date() <= fields.date.today() <= record.date_end.date():
                            rec.current_contract_id = record.id
                            rec.last_renewal_time = record.date_end
                    if recs_sorted:
                        rec.initial_contract_id = recs_sorted.id
            except:
                continue

    @api.onchange('initial_start', 'initial_end', 'current_start', 'current_end')
    def _onchange_initial_start(self):
        """Checking the end date is less than start date"""
        if self.initial_start and self.initial_end and self.initial_start > self.initial_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))
        if self.current_start and self.current_end and self.current_start > self.current_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))

    @api.model
    def create(self, vals):
        """ Function for adding reference number to the sale order line """
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'sale.order.line') or _('New')
        return super(SaleOrderLine, self).create(vals)

    def action_confirm(self):
        """ Button function that confirm the order line products """
        self.rental_status = 'confirmed'

    def action_cancel(self):
        """ Button function that cancel the order """
        self.rental_status = 'cancel'

    def action_renew_contract(self):
        """For renewing the rental order"""
        self.ensure_one()
        vals = []
        if self.rental_contract_ids:
            vals = [{
                'partner_id': rec.partner_id.id,
                'product_id': rec.product_id.id,
                'rental_order_id': rec.rental_order_id.id,
                'sale_order_id': rec.sale_order_id.id,
                'qty': rec.qty,
                'unit_price': rec.unit_price,
            } for rec in self.rental_contract_ids]

        contract_rec = self.env['rental.order.contract'].create(vals)
        return {
            'name': _('Renew Rental Order'),
            'view_mode': 'form',
            'res_model': 'rental.order.contract',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': contract_rec[0].id if contract_rec else False,
        }
