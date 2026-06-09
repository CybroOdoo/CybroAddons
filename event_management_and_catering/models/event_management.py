# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.exceptions import UserError, ValidationError


class EventManagement(models.Model):
    """Model for managing different event kind of events"""
    _name = 'event.management'
    _description = "Event Management"

    name = fields.Char(string='Name', readonly=True, copy=False,
                       help="Show combined name of the event")
    reference = fields.Char(string='Reference', readonly=True,
                            help="Reference of the event")
    type_of_event_id = fields.Many2one('event.management.type',
                                       string="Type",
                                       required=True,
                                       help="Different types of events")
    event_type_image = fields.Image(
        related='type_of_event_id.image',
        store=True,
        readonly=True
    )
    partner_id = fields.Many2one('res.partner', string="Customer",
                                 required=True,
                                 help="Select customers for the event.")
    date = fields.Date(string="Date", default=fields.Date.today, required=True,
                       help="Date of event creating")
    start_date = fields.Datetime(string="Start Date",
                                 default=lambda self: fields.Datetime.now(),
                                 required=True, help="Start date of event")
    end_date = fields.Datetime(string="End Date", required=True,
                               help="End date of the event")
    service_line_ids = fields.One2many('event.service.line',
                                       'event_id',
                                       string="Services", help="Event services")
    state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirmed'),
                              ('invoice', 'Invoiced'),
                              ('close', 'Close'), ('cancel', 'Canceled')],
                             string="State", default="draft",
                             help="States of the Event management record")
    note = fields.Text(string='Terms and Conditions', help="Notes")
    price_subtotal = fields.Float(string='Total',
                                  compute='_compute_price_subtotal',
                                  readonly=True, store=True,
                                  help="Total price of services in service"
                                       " lines")
    image = fields.Binary(string="Image", attachment=True,
                          help="This field holds the image used as image for "
                               "the event, limited to 1080x720px.")
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True,
                                  default=lambda self:
                                  self.env.user.company_id.currency_id,
                                  help="Default currency of company")
    invoice_count = fields.Integer(string='Count of Invoices',
                                   help="Count of total invoices for the event")
    invoice_ids = fields.Many2many("account.move",
                                   string='Invoices', copy=False,
                                   help="Invoices created for each event")
    pending_invoice = fields.Boolean(string="In Voice Pending",
                                     compute='_compute_pending_invoice',
                                     help="Does any pending invoice.")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company.id)
    catering_on = fields.Boolean(string="Catering Active", default=False,
                                 help="Shows thw catering is active or not")
    catering_id = fields.Many2one('event.management.catering',
                                  string="Catering Id",
                                  help="Corresponding catering in event")
    catering_pending = fields.Integer(string='Catering Pending',
                                      compute='_compute_catering_pending',
                                      help="Shows count of catering "
                                           "works are pending")
    catering_done = fields.Integer(string='Catering Done',
                                   compute='_compute_catering_done',
                                   help="Shows how many catering works are "
                                        "done")

    @api.model
    def create(self, vals_list):
        """Create event records with date validation, auto-generated names, and sequence-based references."""
        for values in vals_list:
            # Validate dates
            if values.get('start_date') and values.get('end_date'):
                if values['start_date'] >= values['end_date']:
                    raise UserError(_('Start date must be less than End date'))

            # Build name safely
            partner = self.env['res.partner'].browse(values.get('partner_id'))
            event_type = self.env['event.management.type'].browse(
                values.get('type_of_event_id')
            )

            values['name'] = '%s-%s-%s' % (
                partner.name or '',
                event_type.name or '',
                values.get('date')
            )

            # Sequence
            values['reference'] = self.env['ir.sequence'].next_by_code(
                'event.order.sequence'
            )

        return super(EventManagement, self).create(vals_list)

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_pending(self):
        """ Computes catering_pending field """
        for record in self:
            pending = sum(
                1 for line in record.catering_id.catering_works_ids
                if line.work_status == 'open'
            )
            record.catering_pending = pending

    @api.depends('catering_id.catering_works_ids.work_status')
    def _compute_catering_done(self):
        """Compute the number of completed catering work items linked to the catering order."""
        for record in self:
            done_count = sum(
                1 for line in record.catering_id.catering_works_ids
                if line.work_status == 'done'
            )
            record.catering_done = done_count

    @api.depends('service_line_ids', 'service_line_ids.amount')
    def _compute_price_subtotal(self):
        """ Computes price total """
        total = 0
        for items in self.service_line_ids:
            total += items.amount
        self.price_subtotal = total

    @api.depends('service_line_ids', 'service_line_ids.state')
    def _compute_pending_invoice(self):
        """ Computes pending invoices """
        pending = 0
        for lines in self.service_line_ids:
            if lines.invoiced is False and lines.state == "done":
                pending = 1
        self.pending_invoice = True if pending == 1 else False

    def action_event_confirm(self):
        """Button action to confirm. create catering service
        when confirming event."""
        for rec in self:
            catering_line = rec.service_line_ids.filtered(lambda l: l.service == 'catering')
            if catering_line:
                catering_line = catering_line[0]
                rec.catering_on = True
                rec.catering_id = rec.env['event.management.catering'].create({
                    'name': rec.env['ir.sequence'].next_by_code(
                        'catering.order.sequence'),
                    'start_date': catering_line.date_from,
                    'end_date': catering_line.date_to,
                    'parent_event_id': rec.id,
                    'event_type_id': rec.type_of_event_id.id,
                    'catering_id': catering_line.id,
                }).id
            rec.state = "confirm"

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

    def action_event_invoice_create(self):
        """Button action to create related invoice"""
        product_line = []
        payment_list = []
        for line in self.service_line_ids:
            if line.invoiced is False and line.state == "done":
                product_line.append({'product_id': line.related_product_id,
                                     'price_unit': line.amount})
                line.invoiced = True
        if len(product_line) > 0:
            partner = self.partner_id
            for records in product_line:
                product_id = records['product_id']
                if product_id.property_account_income_id.id:
                    income_account = product_id.property_account_income_id.id
                elif product_id.categ_id.property_account_income_categ_id.id:
                    income_account = product_id.categ_id. \
                        property_account_income_categ_id.id
                else:
                    raise UserError(
                        _('Please define income account for'
                          ' this product: "%s" (id:%d).') % (
                            product_id.name, product_id.id))

                inv_line_data = {
                    'name': self.name,
                    'account_id': income_account,
                    'price_unit': records['price_unit'],
                    'quantity': 1,
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                }
                payment_list.append((0, 0, inv_line_data))
            inv_data = {
                'move_type': 'out_invoice',
                'ref': self.name,
                'bank_partner_id': partner.property_account_payable_id.id,
                'partner_id': partner.id,
                'payment_reference': self.name,
                'company_id': self.env.user.company_id.id,
                'invoice_line_ids': payment_list,
            }
            inv_id = self.env['account.move'].create(inv_data)
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
        return None

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

    def action_view_catering_service(self):
        """
        This function returns an action that display existing catering
        service of the event.
        """
        action = self.env.ref(
            'event_management_and_catering.event_management_catering_action'). \
            sudo().read()[0]
        action['views'] = [(self.env.ref(
            'event_management_and_catering.event_management_catering_view_form').id, 'form')]
        action['res_id'] = self.catering_id.id
        if self.catering_id.id is not False:
            return action
        return False
