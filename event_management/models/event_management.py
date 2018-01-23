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
from odoo.exceptions import UserError, ValidationError


class EventManagement(models.Model):
    _name = 'event.management'

    name = fields.Char(string="Name", readonly=True)
    type_of_event = fields.Many2one('event.management.type', string="Type", required=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True)
    date = fields.Date(string="Date", default=fields.Date.today, required=True)
    start_date = fields.Datetime(string="Start date", default=lambda self: fields.datetime.now(), required=True)
    end_date = fields.Datetime(string="End date", required=True)
    service_line = fields.One2many('event.service.line', 'event_id', string="Services")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'), ('invoice', 'Invoiced'),
                              ('close', 'Close'), ('cancel', 'Canceled')], string="State", default="draft")
    note = fields.Text('Terms and conditions')
    price_subtotal = fields.Float(string='Total', compute='sub_total_update', readonly=True, store=True)
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as image for the event, limited to 1080x720px.")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    invoice_count = fields.Integer(string='# of Invoices')
    invoice_ids = fields.Many2many("account.invoice", string='Invoices', copy=False)
    pending_invoice = fields.Boolean(string="Invoice Pending", compute='pending_invoice_find')

    @api.multi
    @api.depends('service_line', 'service_line.state')
    def pending_invoice_find(self):
        pending = 0
        for lines in self.service_line:
            if lines.invoiced is False and lines.state == "done":
                pending = 1
        if pending == 1:
            self.pending_invoice = True
        else:
            self.pending_invoice = False

    @api.multi
    @api.depends('service_line', 'service_line.amount')
    def sub_total_update(self):
        total = 0
        for items in self.service_line:
            total += items.amount
        self.price_subtotal = total

    @api.model
    def create(self, values):
        start_date = values['start_date']
        end_date = values['end_date']
        if start_date >= end_date:
            raise UserError(_('Start date must be less than End date'))
        sequence_code = 'event.order.sequence'
        sequence_number = self.env['ir.sequence'].next_by_code(sequence_code)
        values['name'] = sequence_number
        return super(EventManagement, self).create(values)

    @api.multi
    def event_confirm(self):
        self.state = "confirm"

    @api.multi
    def event_cancel(self):
        self.state = "cancel"

    @api.multi
    def event_close(self):
        pending = 0
        for lines in self.service_line:
            if lines.invoiced is False:
                pending = 1
        if pending == 1:
            raise ValidationError(_('You can close an event only when all services is Done and Invoiced'))
        else:
            self.state = "close"

    @api.multi
    def action_view_invoice_event(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_invoice_tree1').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [(self.env.ref('account.invoice_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    @api.multi
    def event_invoice_create(self):
        product_line = []
        for lines in self.service_line:
            if lines.invoiced is False and lines.state == "done":
                product_line.append({'product_id': lines.related_product, 'price_unit': lines.amount})
                lines.invoiced = True
        if len(product_line) > 0:
            journal_id = self.env['account.invoice'].default_get(['journal_id'])['journal_id']
            company_id = self.env.user.company_id.id
            inv_obj = self.env['account.invoice']
            inv_line_obj = self.env['account.invoice.line']
            partner = self.partner_id
            inv_data = {
                'name': partner.name,
                'reference': partner.name,
                'account_id': partner.property_account_payable_id.id,
                'partner_id': partner.id,
                'currency_id': self.currency_id.id,
                'journal_id': journal_id,
                'origin': self.name,
                'company_id': company_id,
            }
            inv_id = inv_obj.create(inv_data)
            for records in product_line:
                product_id = records['product_id']
                price_unit = records['price_unit']
                if product_id.property_account_income_id.id:
                    income_account = product_id.property_account_income_id.id
                elif product_id.categ_id.property_account_income_categ_id.id:
                    income_account = product_id.categ_id.property_account_income_categ_id.id
                else:
                    raise UserError(
                        _('Please define income account for this product: "%s" (id:%d).') % (product_id.name,
                                                                                             product_id.id))
                inv_line_data = {
                    'name': self.name,
                    'account_id': income_account,
                    'price_unit': price_unit,
                    'quantity': 1,
                    'product_id': product_id.id,
                    'invoice_id': inv_id.id,
                    'uom_id': product_id.uom_id.id,
                }
                inv_line_obj.create(inv_line_data)
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('account.action_invoice_tree1')
            list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
            form_view_id = imd.xmlid_to_res_id('account.invoice_form')
            result = {
                'name': action.name,
                'help': action.help,
                'type': 'ir.actions.act_window',
                'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'],
                          [False, 'calendar'], [False, 'pivot']],
                'target': action.target,
                'context': action.context,
                'res_model': 'account.invoice',
            }
            if len(inv_id) > 1:
                result['domain'] = "[('id','in',%s)]" % inv_id.ids
            elif len(inv_id) == 1:
                result['views'] = [(form_view_id, 'form')]
                result['res_id'] = inv_id.ids[0]
            else:
                result = {'type': 'ir.actions.act_window_close'}
            self.state = "invoice"
            all_invoice_ids = self.invoice_ids.ids
            all_invoice_ids.append(inv_id.id)
            self.update({'invoice_ids': all_invoice_ids, 'invoice_count': self.invoice_count + 1})
            return result


class EventServiceLine(models.Model):
    _name = 'event.service.line'

    service = fields.Selection([('none', 'None')], string="Services", required=True)
    event_id = fields.Many2one('event.management', string="Event")
    date_from = fields.Datetime(string="Date from", required=True)
    date_to = fields.Datetime(string="Date to", required=True)
    amount = fields.Float(string="Amount", readonly=True)
    state = fields.Selection([('done', 'Done'), ('pending', 'Pending')], string="State", default="pending",
                             readonly=True)
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    invoiced = fields.Boolean(string="Invoiced")
    related_product = fields.Many2one('product.product', string="Related Product")

    _sql_constraints = [('event_supplier_unique', 'unique(event_id, service)',
                         'Duplication Of Service In The Service Lines Is not Allowed')]

    @api.multi
    @api.constrains('date_from', 'date_to')
    def _check_date_to_date_from(self):
        if self.date_to < self.date_from:
            raise ValidationError(_('"Date to" cannot be set before "Date from".\n\n'
                                    'Check the "Date from" and "Date to" of the "%s" service' % self.service))


class EventManagementType(models.Model):
    _name = 'event.management.type'

    name = fields.Char(string="Name")
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as image for the event, limited to 1080x720px.")
    event_count = fields.Integer(string="# of Events", compute='event_count_calculation')

    @api.multi
    def event_count_calculation(self):
        for records in self:
            events = self.env['event.management'].search([('type_of_event', '=', records.id)])
            records.event_count = len(events)
