# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import fields, models, api, _, exceptions
from datetime import datetime
from odoo.exceptions import ValidationError


class ReservationInvoice(models.Model):
    _inherit = 'account.move'

    @api.model
    def create(self, vals):
        res = super(ReservationInvoice, self).create(vals)
        if self._context.get("reservation_id"):
            reserv = self.env["room.reservation"].browse(self._context["reservation_id"])
            reserv.write({"invoice_id": res.id, "invoice_status": "invoiced"})
        return res


class Reservation(models.Model):
    _name = "room.reservation"
    _description = 'Reservation'
    _rec_name = 'name'

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    num_person = fields.Integer(string='Number of Persons', default=1,required=True)
    reservation_line_ids = fields.One2many('room.reservation.line', "reservation_id", string='Booking Info')
    state = fields.Selection([('draft', 'Draft'), ('confirm',
                                                   'Confirm'), ('occupied', 'Occupied'), ('done', 'Done'),
                              ('cancel', 'Cancel')],
                             default='draft')

    sale_order_id = fields.Many2one('sale.order', 'sale Order', delegate=True, copy=False, ondelete="cascade")
    service_ids = fields.One2many('hotel.service.line', 'reservation_id')
    invoice_id = fields.Many2one('account.move')
    meals_ids = fields.One2many('hotel.meals.line', 'reservation_id')

    def action_confirm(self):
        self.write({'state': 'confirm'})
        self.sale_order_id.write({'invoice_status': 'to invoice', 'state': 'sale'})

    def action_cancel(self):
        self.state = 'cancel'
        for rec in self.reservation_line_ids:
            rec.room_id.write({'status': 'available'})

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'room.reservation') or _('New')
        persons = 0
        for rec in vals['reservation_line_ids']:
            room_type = self.env['room.types'].sudo().search([('categ_id','=',rec[2]['type_id'])])
            persons += room_type.num_person
        if vals.get('num_person') > persons:
            raise ValidationError(_("Number of persons out of limit!"))
        return super(Reservation, self).create(vals)


class ReservationLine(models.Model):
    _name = "room.reservation.line"
    _description = 'Reservation Lines'

    reservation_id = fields.Many2one('room.reservation', ondelete="cascade")
    type_id = fields.Many2one('product.category', string='Room type')
    room_id = fields.Many2one('room.room', string='room Number')
    checkin_date = fields.Date(string='Checkin Date', required=True)
    checkout_date = fields.Date(string='Checkout Date', required=True)
    order_line_id = fields.Many2one('sale.order.line', 'sale Order Line', delegate=True, copy=False, ondelete="cascade")

    @api.constrains("checkin_date", "checkout_date")
    def _check_dates(self):
        if self.checkin_date >= self.checkout_date:
            raise ValidationError(_(" Check In Date Should be less than the Check Out Date!"))

        if self.reservation_id.date_order and self.checkin_date:
            if self.checkin_date < self.reservation_id.date_order.date():
                raise ValidationError(_("check in date should be greater than the current date."))

    @api.model
    def create(self, vals):
        room = self.env['room.room'].sudo().search([('product_id', '=', vals['product_id'])])
        vals['room_id'] = room.id
        room.write({'status': 'book'})
        if "reservation_id" in vals:
            reserv = self.env["room.reservation"].browse(vals["reservation_id"])
            vals.update({"order_id": reserv.sale_order_id.id})
        duplicate = self.env['room.reservation.line'].sudo().search(
            [
                ('product_id', '=', vals['product_id']), ('reservation_id', '!=', vals['reservation_id']),
                ('checkin_date', '>=', vals['checkin_date']), ('checkin_date', '<=', vals['checkout_date']),
                ('checkout_date', '<=', vals['checkout_date']), ('checkout_date', '>=', vals['checkin_date']),
                ('reservation_id.state', 'in', ('confirm', 'occupied'))
            ])
        if duplicate:
            raise ValidationError(_('Room not available'))

        return super(ReservationLine, self).create(vals)

    def write(self, vals):
        if "reservation_id" in vals:
            reserv = self.env["room.reservation"].browse(vals["reservation_id"])
            vals.update({"order_id": reserv.sale_order_id.id})
        return super(ReservationLine, self).write(vals)

    @api.onchange('type_id')
    def room_clear(self):
        self.write({'product_id': [(5,)]}, )

    @api.onchange('checkin_date', 'checkout_date')
    def _compute_days(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                fmt = '%Y-%m-%d'
                date_difference = (rec.checkout_date - rec.checkin_date)
                float_days = date_difference.days + float(date_difference.seconds) / 86400
                rec.product_uom_qty = float_days

    @api.onchange('product_id')
    def _compute_subtotoal(self):
        self.price_unit = self.product_id.list_price
        self.tax_id = self.product_id.taxes_id


class ServiceLine(models.Model):
    _name = "hotel.service.line"
    _description = 'service Lines'

    order_line_id = fields.Many2one('sale.order.line', "Services", required=True, delegate=True, ondelete="cascade")
    reservation_id = fields.Many2one("room.reservation", ondelete="cascade")
    categ_id = fields.Many2one(related='product_id.categ_id')
    checkin_date = fields.Datetime("From Date")
    checkout_date = fields.Datetime("To Date")

    @api.model
    def create(self, vals):
        self.price_unit = self.product_id.list_price
        if "reservation_id" in vals:
            reserv = self.env["room.reservation"].browse(vals["reservation_id"])
            vals.update({"order_id": reserv.sale_order_id.id})
        return super(ServiceLine, self).create(vals)

    @api.onchange('product_id')
    def _compute_subtotal(self):
        self.price_unit = self.product_id.list_price


class MealsLine(models.Model):
    _name = "hotel.meals.line"
    _description = 'Meals Lines'

    order_line_id = fields.Many2one('sale.order.line', "Services", required=True, delegate=True, ondelete="cascade")
    reservation_id = fields.Many2one("room.reservation", ondelete="cascade")
    categ_id = fields.Many2one('product.category', string='Type')
    checkin_date = fields.Datetime("From Date")
    checkout_date = fields.Datetime("To Date")

    @api.model
    def create(self, vals):
        self.price_unit = self.product_id.list_price
        if "reservation_id" in vals:
            reserv = self.env["room.reservation"].browse(vals["reservation_id"])
            vals.update({"order_id": reserv.sale_order_id.id})
        return super(MealsLine, self).create(vals)

    @api.onchange('product_id')
    def _compute_subtotal(self):
        self.price_unit = self.product_id.list_price

    @api.onchange('categ_id')
    def room_clear(self):
        self.write({'product_id': [(5,)]}, )

    @api.onchange('checkin_date', 'checkout_date')
    def _compute_days(self):
        for rec in self:
            if rec.checkin_date and rec.checkout_date:
                fmt = '%Y-%m-%d'
                date_difference = (rec.checkout_date - rec.checkin_date)
                float_days = date_difference.days + float(date_difference.seconds) / 86400
                self.price_subtotal = self.price_unit * float_days
                self.product_uom_qty = float_days
