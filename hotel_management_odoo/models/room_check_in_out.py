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
    rm_id = fields.Many2one('room.reservation.line', domain="[('reservation_id','=',reservation_id)]", string="Room No",required=True)
    reservation_id = fields.Many2one('room.reservation', string='Reservation ',required=True,
                                     domain="[('state','=','confirm')]")
    state = fields.Selection([('draft', 'Draft'),('done', 'Done')],
                             default='draft')

    def action_checkin(self):
        self.rm_id.room_id.write({'status': 'occupied'})
        self.reservation_id.write({'state': 'occupied'})
        self.state='done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'room.checkin') or _('New')
        return super(RoomCheckin, self).create(vals)


class RoomCheckout(models.Model):
    _name = "room.checkout"
    _description = 'Room Checkout'

    name = fields.Char(string='Check-Out Reference',required=True, copy=False, readonly=True,
                       default=lambda self: _('New'))
    rm_id = fields.Many2one('room.reservation.line', domain="[('reservation_id','=',reservation_id)]", string="Room No",required=True)
    reservation_id = fields.Many2one('room.reservation', string='Reservation', domain="[('state','=','occupied')]",required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')],
                             default='draft')

    def action_checkout(self):
        self.rm_id.room_id.write({'status': 'available'})
        reserv_line = self.env['room.reservation.line'].sudo().search([('reservation_id', '=', self.reservation_id.id)])
        status = 'available'
        for rec in reserv_line:
            if rec.room_id.status == 'available':
                break
            else:
                status = 'occupied'
        if status == 'available':
            self.reservation_id.write({'state': 'done'})
        self.state = 'done'

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'room.checkout') or _('New')

        return super(RoomCheckout, self).create(vals)
