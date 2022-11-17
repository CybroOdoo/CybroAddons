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
from odoo import fields, models, api, _


class RoomCheckin(models.Model):
    _name = "room.checkin"
    _description = 'Room Checkin'

    name = fields.Char(string='Check-In Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    rm_ids = fields.Many2many('room.reservation.line',
                              domain="[('reservation_id','=',reservation_id)]",
                              string="Room No",
                              required=True)
    reservation_id = fields.Many2one('room.reservation', string='Reservation ', required=True,
                                     domain="[('state','=','confirm')]")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft')

    @api.onchange('reservation_id')
    def _rm_ids(self):
        res_line = []
        if self.reservation_id.reservation_line_ids:
            for line in self.reservation_id.reservation_line_ids:
                if line.room_id.status == 'book':
                    res_line.append(line.id)
        return {'domain': {'rm_ids': [('id', 'in', res_line)]}}

    def action_checkin(self):
        for rec in self.rm_ids: rec.room_id.write({'status': 'occupied'})
        state = self.reservation_id.reservation_line_ids.mapped('room_id')
        rs_flag = True
        for rec in state:
            if rec.status == 'occupied':
                rs_flag = True
            else:
                rs_flag = False
                break
        if rs_flag:
            self.reservation_id.write({'state': 'occupied'})
        self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'room.checkin') or _('New')
        return super(RoomCheckin, self).create(vals)


class RoomCheckout(models.Model):
    _name = "room.checkout"
    _description = 'Room Checkout'

    name = fields.Char(string='Check-Out Reference', required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    rm_ids = fields.Many2many('room.reservation.line', domain="[('reservation_id','=',reservation_id)]",
                              string="Room No",
                              required=True)
    reservation_id = fields.Many2one('room.reservation', string='Reservation', domain="[('state','=','occupied')]",
                                     required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft')

    @api.onchange('reservation_id')
    def _rm_ids(self):
        res_line = []
        if self.reservation_id.reservation_line_ids:
            for line in self.reservation_id.reservation_line_ids:
                if line.room_id.status == 'occupied':
                    res_line.append(line.id)
        return {'domain': {'rm_ids': [('id', 'in', res_line)]}}

    def action_checkout(self):
        for rec in self.rm_ids: rec.room_id.write({'status': 'available'})
        state = self.reservation_id.reservation_line_ids.mapped('room_id')
        rs_flag = True
        for rec in state:
            if rec.status == 'available':
                rs_flag = True
            else:
                rs_flag = False
                break
        if rs_flag:
            self.reservation_id.write({'state': 'done'})
        self.state = 'done'


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'room.checkout') or _('New')

        return super(RoomCheckout, self).create(vals)
