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


class SaleOrder(models.Model):
    """Inherit the sale order to add new features"""
    _inherit = 'sale.order'

    rental_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'),
         ('cancel', 'Cancelled')],
        default='new', string='Rental Status',
        help='To showing the rental status of the order')

    def action_confirm(self):
        """For creating rental order contract at the time of confirm the sale order"""
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
    """Inherit sale order line to add contract details on the sale order line form view"""
    _inherit = 'sale.order.line'
    _rec_name = 'reference_no'

    reference_no = fields.Char(string='Reference', copy=False,
                               readonly=True, default=lambda self: _('New'),
                               help='Showing the reference number of sale '
                                    'order line')
    initial_contract_id = fields.Many2one('rental.order.contract',
                                          string='Initial Contract',
                                          help='To add initial contract')
    initial_start = fields.Datetime(string='Start Date',
                                    help='Initial start date of Rental Order '
                                         'Contract',
                                    related='initial_contract_id.date_start')
    initial_end = fields.Datetime(string='End Date',
                                  help='Initial end date of Rental Order '
                                       'Contract',
                                  related='initial_contract_id.date_end')
    initial_qty = fields.Float(string='Quantity',
                               help='Quantity of initial contract',
                               related='initial_contract_id.qty')
    current_contract_id = fields.Many2one('rental.order.contract',
                                          string='Current Contract',
                                          help='To add the current contract')
    partner_id = fields.Many2one('res.partner', string='Partner',
                                 help='Partner of the corresponding sale order')
    current_start = fields.Datetime(string='Start Date',
                                    help='Current contract start date',
                                    related='current_contract_id.date_start')
    current_end = fields.Datetime(string='End Date',
                                  help='Current contract end date',
                                  related='current_contract_id.date_end')
    current_qty = fields.Float(string='Quantity',
                               help='Current contract product quantity',
                               related='current_contract_id.qty')
    last_renewal_time = fields.Datetime(string='Last Renewal Time',
                                        help='Last Date contract Renewal')
    is_rental = fields.Boolean(string='Is Rental',
                               help='To check the order is rental or not')
    rental = fields.Boolean(string='Rental', related='product_id.rental',
                            help='To check the order line product is rental '
                                 'or not')
    current_contract_values = fields.Boolean(string='Initial',
                                             compute='_compute_current_contract_values',
                                             help='To Update the values')
    rental_status = fields.Selection(
        [('new', 'New'), ('confirmed', 'Confirmed'),
         ('cancel', 'Cancelled')],
        default='new', string='Rental Status',
        help='To showing the rental status of the order')
    rental_contract_ids = fields.One2many('rental.order.contract',
                                          'rental_order_id',
                                          string='Rental Contract',
                                          help='To showing the rental order '
                                               'contract')

    def _compute_current_contract_values(self):
        """For fetching the current contract values to the sale order line
        form view"""
        for rec in self:
            rec.current_contract_values = False
            try:
                recs_sorted = \
                    rec.rental_contract_ids.sorted(key=lambda r: r.date_start)[
                        0] if rec.rental_contract_ids.sorted(
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

    @api.onchange('initial_start', 'initial_end', 'current_start',
                  'current_end')
    def _onchange_initial_start(self):
        """Checking whether the end date is less than or equal to the start date"""
        if self.initial_start and self.initial_end and self.initial_start > self.initial_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))
        if self.current_start and self.current_end and self.current_start > self.current_end:
            raise UserError(
                _('The end date must be after or the same as the start date'))

    @api.model
    def create(self, vals):
        """For adding references number to sale order line"""
        if vals.get('reference_no', _('New')) == _('New'):
            vals['reference_no'] = self.env['ir.sequence'].next_by_code(
                'sale.order.line') or _('New')
        return super(SaleOrderLine, self).create(vals)

    def action_confirm(self):
        """ Function for confirm the order line"""
        self.rental_status = 'confirmed'

    def action_cancel(self):
        """ Function for cancel sale order """
        self.rental_status = 'cancel'

    def action_renew_contract(self):
        """For renewing the rental order
            :param :
            :return: rental order renewing form view
        """
        self.ensure_one()
        vals = []
        for rec in self.rental_contract_ids[
            0] if self.rental_contract_ids else '':
            vals.append({
                'partner_id': rec.partner_id.id,
                'product_id': rec.product_id.id,
                'rental_order_id': rec.rental_order_id.id,
                'sale_order_id': rec.sale_order_id.id,
                'qty': rec.qty,
                'unit_price': rec.unit_price,
            })
        contract_rec = self.env['rental.order.contract'].create(vals)
        return {
            'name': _('Renew Rental Order'),
            'view_mode': 'form',
            'res_model': 'rental.order.contract',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': contract_rec.id,
        }
