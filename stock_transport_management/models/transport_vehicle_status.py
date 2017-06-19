# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Saritha Sahadevan(<https://www.cybrosys.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <https://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields


class VehicleStatus(models.Model):
    _name = 'vehicle.status'

    name = fields.Char(string="Vehicle Name", required=True)
    transport_date = fields.Date(string="Transportation Date")
    no_parcels = fields.Char(string="No Of Parcels")
    sale_order = fields.Char(string='Order Reference')
    delivery_order = fields.Char(string="Delivery Order")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('start', 'Start'),
        ('waiting', 'Waiting'),
        ('cancel', 'Cancel'),
        ('done', 'Done'),
    ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

    def start_action(self):
        vehicle = self.env['sale.vehicle'].search([('name', '=', self.name)])
        vals = {'active_available': False}
        vehicle.write(vals)
        self.write({'state': 'start'})

    def action_cancel(self):
        self.write({'state': 'cancel'})
        vehicle = self.env['sale.vehicle'].search([('name', '=', self.name)])
        vals = {'active_available': True}
        vehicle.write(vals)

    def action_done(self):
        self.write({'state': 'done'})
        vehicle = self.env['sale.vehicle'].search([('name', '=', self.name)])
        vals = {'active_available': True}
        vehicle.write(vals)

    def action_waiting(self):
        vehicle = self.env['sale.vehicle'].search([('name', '=', self.name)])
        vals = {'active_available': False}
        vehicle.write(vals)
        self.write({'state': 'waiting'})

    def action_reshedule(self):
        self.write({'state': 'draft'})



