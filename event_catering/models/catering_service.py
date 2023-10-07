# -*- coding: utf-8 -*-
###################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
    """Adding catering details in Event management model"""
    _inherit = 'event.management'

    catering_on = fields.Boolean(string="Catering Active", default=False)
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id")
    catering_pending = fields.Integer(string='Catering Pending',
                                      compute='_compute_catering_pending')
    catering_done = fields.Integer(string='Catering Done',
                                   compute='_compute_catering_done')

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_pending(self):
        self.catering_pending = False
        for order in self.catering_id:
            pending = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'open':
                    pending += 1
            self.catering_pending = pending

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_done(self):
        self.catering_done = False
        for order in self.catering_id:
            done = 0
            for lines in order.catering_works_ids:
                if lines.work_status == 'done':
                    done += 1
            self.catering_done = done

    def action_event_confirm(self):
        """Confirm the Event"""
        catering_service = self.env['event.management.catering']
        catering_line = self.service_line_ids.search([
            ('service_id', '=', 'Catering'), ('event_id', '=', self.id)])
        if len(catering_line) > 0:
            self.catering_on = True
            sequence_code = 'catering.order.sequence'
            name = self.env['ir.sequence'].next_by_code(sequence_code)
            event = self.id
            event_type = self.type_of_event_id.id
            start_date = catering_line.date_from
            end_date = catering_line.date_to
            catering_id = catering_line.id
            data = {
                'name': name,
                'start_date': start_date,
                'end_date': end_date,
                'parent_event_id': event,
                'event_type_id': event_type,
                'catering_id': catering_id,
            }
            catering_map = catering_service.create(data)
            self.catering_id = catering_map.id
        super(EventManagementInherit, self).action_event_confirm()

    def action_view_catering_service(self):
        """This function returns an action that display existing catering
        service of the event."""
        action = self.env.ref(
            'event_catering.event_management_catering_action_view_kanban').sudo().read()[
            0]
        action['views'] = [(self.env.ref(
            'event_catering.event_management_catering_view_form').id, 'form')]
        action['res_id'] = self.catering_id.id
        if self.catering_id.id is not False:
            return action


class EventManagementCatering(models.Model):
    """Model for creating catering services"""
    _name = 'event.management.catering'

    name = fields.Char(string="Name", readonly=True)
    date = fields.Date(string="Date", default=fields.Date.today, readonly=True)
    start_date = fields.Datetime(string="Start date", readonly=True)
    end_date = fields.Datetime(string="End date", readonly=True)
    catering_works_ids = fields.One2many('event.catering.works', 'catering_id',
                                         string="Catering Works")
    state = fields.Selection([('open', 'Open'), ('done', 'Done')],
                             string="State", default="open")
    note = fields.Text(string="Terms and conditions")
    price_subtotal = fields.Float(string='Total',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True)
    parent_event_id = fields.Many2one('event.management', string="Event",
                                      readonly=True)
    catering_id = fields.Integer(string="Catering Id")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id)
    event_type_id = fields.Many2one('event.management.type',
                                    string="Event Type", readonly=True)

    @api.depends('catering_works_ids')
    def _compute_price_subtotal(self):
        total = 0
        for items in self.catering_works_ids:
            total += items.quantity * items.amount
        self.price_subtotal = total

    def action_catering_done(self):
        """ Button action for state change to Done"""
        for items in self.catering_works_ids:
            if items.work_status == 'open':
                raise UserError(_("Catering works are pending"))
        related_product = self.env.ref(
            'event_management.catering_service_product').id
        for items in self.sudo().parent_event_id.service_line_ids:
            if items.id == self.sudo().catering_id:
                items.sudo().write({'amount': self.price_subtotal,
                                    'state': 'done',
                                    'related_product_id': related_product})
        self.state = "done"


class EventCateringWorks(models.Model):
    """Deals with catering works"""
    _name = 'event.catering.works'

    service_id = fields.Many2one('product.product', string="Services",
                                 required=True)
    quantity = fields.Float(string="Quantity", default=1)
    amount = fields.Float(string="Amount")
    sub_total = fields.Float(string="Sub Total", compute="_compute_sub_total",
                             readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id)
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id")
    work_status = fields.Selection([('open', 'Open'), ('done', 'Done')],
                                   string="Work Status", default='open')

    @api.onchange('service_id')
    def _onchange_service_id(self):
        self.amount = self.service_id.lst_price

    @api.depends('quantity', 'amount')
    def _compute_sub_total(self):
        for rec in self:
            rec.sub_total = rec.quantity * rec.amount

    def action_work_completed(self):
        """Button action for completed works"""
        if self.catering_id.state == "open":
            self.work_status = 'open'

    def action_not_completed(self):
        """Button action for non completed works"""
        if self.catering_id.state == "open":
            self.work_status = 'done'


class ProductProduct(models.Model):
    """Inherited the model for adding a field"""
    _inherit = 'product.product'

    is_catering = fields.Boolean(string="Catering Product",
                                 help='For specifying the catering product')
