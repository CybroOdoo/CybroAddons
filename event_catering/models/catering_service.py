# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2017-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Avinash Nk(<avinash@cybrosys.in>)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class EventManagementInherit(models.Model):
    _inherit = 'event.management'

    catering_on = fields.Boolean(string="Catering Active", default=False)
    catering_id = fields.Many2one('event.management.catering', string="Catering Id")
    catering_pending = fields.Integer(string='Catering Pending', compute='compute_catering_pending')
    catering_done = fields.Integer(string='Catering Done', compute='compute_catering_done')

    @api.multi
    def compute_catering_pending(self):
        for order in self.catering_id:
            pending = 0
            for lines in order.catering_works:
                if lines.work_done is False:
                    pending += 1
            self.catering_pending = pending

    @api.multi
    def compute_catering_done(self):
        for order in self.catering_id:
            done = 0
            for lines in order.catering_works:
                if lines.work_done is True:
                    done += 1
            self.catering_done = done

    @api.multi
    def event_confirm(self):
        catering_service = self.env['event.management.catering']
        catering_line = self.service_line.search([('service', '=', 'catering'), ('event_id', '=', self.id)])
        if len(catering_line) > 0:
            self.catering_on = True
            sequence_code = 'catering.order.sequence'
            name = self.env['ir.sequence'].next_by_code(sequence_code)
            event = self.id
            event_type = self.type_of_event.id
            start_date = catering_line.date_from
            end_date = catering_line.date_to
            catering_id = catering_line.id
            data = {
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'parent_event': event,
                'event_type': event_type,
                'catering_id': catering_id,
            }
            catering_map = catering_service.create(data)
            self.catering_id = catering_map.id
        super(EventManagementInherit, self).event_confirm()

    @api.multi
    def action_view_catering_service(self):
        """This function returns an action that display existing catering service
            of the event."""
        action = self.env.ref('event_catering.event_catering_action').read()[0]
        action['views'] = [(self.env.ref('event_catering.event_catering_form_view').id, 'form')]
        action['res_id'] = self.catering_id.id
        if self.catering_id.id is not False:
            return action


class EventService(models.Model):
    _inherit = 'event.service.line'

    service = fields.Selection(selection_add=[('catering', 'Catering')])


class EventManagementCatering(models.Model):
    _name = 'event.management.catering'

    name = fields.Char(string="Name", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today, readonly=True)
    start_date = fields.Datetime(string="Start date", readonly=True)
    end_date = fields.Datetime(string="End date", readonly=True)
    catering_works = fields.One2many('event.catering.works', 'catering_id', string="Catering Works")
    state = fields.Selection([('open', 'Open'), ('done', 'Done')], string="State", default="open")
    note = fields.Text(string="Terms and conditions")
    price_subtotal = fields.Float(string='Total', compute='sub_total_update', readonly=True, store=True)
    parent_event = fields.Many2one('event.management', string="Event", readonly=True)
    catering_id = fields.Integer(string="Catering Id")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    event_type = fields.Many2one('event.management.type', string="Event Type", readonly=True)

    @api.multi
    @api.depends('catering_works')
    def sub_total_update(self):
        total = 0
        for items in self.catering_works:
            total += items.quantity * items.amount
        self.price_subtotal = total

    @api.multi
    def catering_done(self):
        for items in self.catering_works:
            if items.work_done is False:
                raise UserError(_("Catering works are pending"))
        related_product = self.env.ref('event_catering.catering_service_product').id
        for items in self.sudo().parent_event.service_line:
            if items.id == self.sudo().catering_id:
                items.sudo().write({'amount': self.price_subtotal, 'state': 'done', 'related_product': related_product})
        self.state = "done"


class EventCateringWorks(models.Model):
    _name = 'event.catering.works'

    service = fields.Many2one('product.product', string="Services", required=True)
    quantity = fields.Float(string="Quantity", default=1)
    amount = fields.Float(string="Amount")
    sub_total = fields.Float(string="Sub Total", compute="sub_total_computation", readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    catering_id = fields.Many2one('event.management.catering', string="Catering Id")
    work_done = fields.Boolean(string="Work done", default=False)

    @api.onchange('service')
    def onchange_service(self):
        self.amount = self.service.lst_price

    @api.one
    @api.depends('quantity', 'amount')
    def sub_total_computation(self):
        self.sub_total = self.quantity * self.amount

    @api.multi
    def work_completed(self):
        if self.catering_id.state == "open":
            self.work_done = False

    @api.multi
    def not_completed(self):
        if self.catering_id.state == "open":
            self.work_done = True
