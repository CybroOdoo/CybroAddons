# -*- coding: utf-8 -*-
"""Event Management"""
import mailbox
################################################################################
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
################################################################################
from ast import literal_eval
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class EventManagement(models.Model):
    """Model for managing Event Management"""
    _name = 'event.management'

    name = fields.Char('Name', readonly=True, copy=False)
    ref = fields.Char(string='Ref', readonly=True)
    type_of_event_id = fields.Many2one('event.management.type', string="Type",
                                       required=True)
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True)
    date = fields.Date(string="Date", default=fields.Date.today, required=True)
    start_date = fields.Datetime(string="Start date",
                                 default=lambda self: fields.datetime.now(),
                                 required=True)
    end_date = fields.Datetime(string="End date", required=True)
    service_line_ids = fields.One2many('event.service.line', 'event_id',
                                       string="Services")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'),
                              ('close', 'Close'), ('cancel', 'Canceled')],
                             string="State", default="draft")
    note = fields.Text('Terms and conditions')
    price_subtotal = fields.Float(string='Total',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True)
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as image for "
                               "the event, limited to 1080x720px.")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id)
    invoice_count = fields.Integer(string='# of Invoices')
    invoice_ids = fields.Many2many("account.move", string='Invoices',
                                   copy=False)
    pending_invoice = fields.Boolean(string="Invoice Pending",
                                     compute='_compute_pending_invoice')

    @api.depends('service_line_ids', 'service_line_ids.state')
    def _compute_pending_invoice(self):
        pending = 0
        for lines in self.service_line_ids:
            if lines.invoiced is False and lines.state == "done":
                pending = 1
        if pending == 1:
            self.pending_invoice = True
        else:
            self.pending_invoice = False

    @api.depends('service_line_ids', 'service_line_ids.amount')
    def _compute_price_subtotal(self):
        total = 0
        for items in self.service_line_ids:
            total += items.amount
        self.price_subtotal = total

    @api.model
    def create(self, values):
        """Crete method for sequencing and checking dates while creating"""
        start_date = values['start_date']
        end_date = values['end_date']
        partner_name = self.env['res.partner'].browse(values['partner_id']).name
        event_name = self.env['event.management.type'].browse(
            values['type_of_event_id']).name
        if start_date >= end_date:
            raise UserError(_('Start date must be less than End date'))

        name = '%s-%s-%s' % (partner_name, event_name, values['date'])
        values['name'] = name
        sequence_code = 'event.order.sequence'
        sequence_number = self.env['ir.sequence'].next_by_code(sequence_code)
        values['ref'] = sequence_number
        res = super(EventManagement, self).create(values)
        return res

    def action_event_confirm(self):
        """Button action to confirm"""
        self.state = "confirm"
        for lines in self.service_line_ids:
            if lines.state == 'pending':
                lines.is_pending = True

    def action_event_cancel(self):
        """Button action to cancel"""
        self.state = "cancel"

    def action_event_close(self):
        """Button action to close"""
        pending = 0
        for lines in self.service_line_ids:
            if lines.invoiced is False:
                pending = 1
        if pending == 1:
            raise ValidationError(_('You can close an event only when all '
                                    'services is Done and Invoiced'))
        else:
            self.state = "close"

    def action_view_invoice_event(self):
        """Button action to View the related invoice"""
        invoices = self.mapped('invoice_ids')
        action = self.env.ref(
            'account.action_move_out_invoice_type').sudo().read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            action['views'] = [
                (self.env.ref('account.view_move_form').id, 'form')]
            action['res_id'] = invoices.ids[0]
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

    def action_event_invoice_create(self):
        """Button action to create related invoice"""
        if self.service_line_ids.filtered(lambda x: x.state == 'pending'):
            raise ValidationError(_('You can create the invoice only when all '
                                    'services is Done'))
        else:
            product_line = []
            payment_list = []
            related_product = self.env.ref(
                'event_management.catering_service_product').id
            product_id = self.env['product.product'].browse(related_product)
            for line in self.service_line_ids:
                if line.invoiced is False and line.state == "done":
                    product_line.append({'product_id': product_id,
                                         'price_unit': line.amount})
                    line.invoiced = True
            if len(product_line) > 0:
                invoice = self.env['account.move']
                move_type = 'out_invoice'
                invoice = invoice.with_context(default_move_type=move_type)
                journal_id = invoice._compute_journal_id()
                company_id = self.env.user.company_id.id
                inv_obj = self.env['account.move']
                partner = self.partner_id
                for records in product_line:
                    product_id = records['product_id']
                    price_unit = records['price_unit']
                    if product_id.property_account_income_id.id:
                        income_account = product_id.property_account_income_id.id
                    elif product_id.categ_id.property_account_income_categ_id.id:
                        income_account = product_id.categ_id.property_account_income_categ_id.id
                    else:
                        raise UserError(
                            _('Please define income account for'
                              ' this product: "%s" (id:%d).') % (
                                product_id.name, product_id.id))

                    inv_line_data = {
                        'name': self.name,
                        'account_id': income_account,
                        'price_unit': price_unit,
                        'quantity': 1,
                        'product_id': product_id.id,
                        'product_uom_id': product_id.uom_id.id,
                    }
                    payment_list.append((0, 0, inv_line_data))
                inv_data = {
                    'move_type': move_type,
                    'ref': self.name,
                    'bank_partner_id': partner.property_account_payable_id.id,
                    'partner_id': partner.id,
                    'payment_reference': self.name,
                    'company_id': company_id,
                    'invoice_line_ids': payment_list,
                }
                inv_id = inv_obj.create(inv_data)
                result = {
                    'view_type': 'form',
                    'res_model': 'account.move',
                    'res_id': inv_id.id,
                    'view_id': False,
                    'view_mode': 'form',
                    'type': 'ir.actions.act_window'
                }
                self.state = "invoice"
                all_invoice_ids = self.invoice_ids.ids
                all_invoice_ids.append(inv_id.id)
                self.update({'invoice_ids': all_invoice_ids,
                             'invoice_count': self.invoice_count + 1})
                return result


class EventServiceLine(models.Model):
    """Model to manage the service lines of the event management"""
    _name = 'event.service.line'

    service_id = fields.Many2one('event.services', string="Services")
    event_id = fields.Many2one('event.management', string="Event")
    date_from = fields.Datetime(string="Date from", required=True)
    date_to = fields.Datetime(string="Date to", required=True)
    amount = fields.Float(string="Amount")
    state = fields.Selection([('done', 'Done'), ('pending', 'Pending')],
                             string="State")
    currency_id = fields.Many2one('res.currency', readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id)
    invoiced = fields.Boolean(string="Invoiced", readonly=True)
    related_product_id = fields.Many2one('product.product',
                                         string="Related Product")
    is_pending = fields.Boolean(string="Pending")

    _sql_constraints = [('event_supplier_unique', 'unique(event_id, service)',
                         'Duplication Of Service In The Service Lines '
                         'Is not Allowed')]

    @api.constrains('date_from', 'date_to')
    def _check_date_to_date_from(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_('"Date to" cannot be set before '
                                        '"Date from".\n\n'
                                        'Check the "Date from" and "Date to" '
                                        'of the "%s" service' % rec.service_id))


class EventService(models.Model):
    _name = 'event.services'

    name = fields.Char(string='Services')


class EventManagementType(models.Model):
    """Model for managing the Event types"""
    _name = 'event.management.type'

    name = fields.Char(string="Name")
    image = fields.Binary("Image", attachment=True,
                          help="This field holds the image used as "
                               "image for the event, limited to 1080x720px.")
    event_count = fields.Integer(string="# of Events",
                                 compute='_compute_event_count')

    def _compute_event_count(self):
        for records in self:
            events = self.env['event.management'].search([
                ('type_of_event_id', '=', records.id)])
            records.event_count = len(events)

    def _get_action(self, action_xml_id):
        action = self.env['ir.actions.actions']._for_xml_id(action_xml_id)
        if self:
            action['display_name'] = self.display_name
        context = {
            'search_default_type_of_event_id': [self.id],
            'default_type_of_event_id': self.id,
        }

        action_context = literal_eval(action['context'])
        context = {**action_context, **context}
        action['context'] = context
        return action

    def get_event_type_action_event(self):
        return self._get_action(
            'event_management.event_management_action_view_kanban')
