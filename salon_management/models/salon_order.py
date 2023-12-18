# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from datetime import date, datetime, timedelta
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError, ValidationError


class SalonOrder(models.Model):
    """Model to create salon orders"""
    _name = 'salon.order'
    _description = 'Salon Order'

    name = fields.Char(string='Salon', required=True, copy=False, readonly=True,
                       default='Draft Salon Order', help="Name of salon order")
    start_time = fields.Datetime(
        string="Start time", default=fields.Datetime.now, required=True,
        help="Start time of the order")
    end_time = fields.Datetime(string="End time", help="End time of the order")
    date = fields.Datetime(string="Date", required=True,
                           default=fields.Datetime.now, help="Registering date")
    color = fields.Integer(string="Color", default=6,
                           help="Color for the order")
    partner_id = fields.Many2one(
        'res.partner', string="Customer", required=False,
        help="If the customer is a regular customer, then you can add the"
             " customer in your database")
    customer_name = fields.Char(string="Name", required=True,
                                help="Name of salon customer")
    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True,
        default=lambda self: self.env.user.company_id.currency_id.id,
        help="Currency used in the order")
    chair_id = fields.Many2one('salon.chair', string="Chair",
                               required=True, help="Chair for the current "
                                                   "order")
    price_subtotal = fields.Monetary(string='Total', readonly=True, store=True,
                                     compute='_compute_price_subtotal',
                                     help="Total price of order")
    time_taken_total = fields.Float(string='Total time',
                                    help='Total time taken')
    note = fields.Text(string='Terms and conditions',
                       help="Note for current order")
    order_line_ids = fields.One2many(comodel_name='salon.order.line',
                                     inverse_name='salon_order_id',
                                     string="Order Lines", copy=True,
                                     help='Salon order line for add '
                                          'list of services', required=True)
    stage_id = fields.Many2one(comodel_name='salon.stage', string="Stages",
                               group_expand='_read_group_stage_ids', default=1,
                               copy=False, help="state for the salon order(user"
                                                " can add dynamic state from"
                                                " the kanban view)")
    inv_stage_identifier = fields.Boolean(string="Stage Identifier",
                                          help="Field to detect stage")
    validation_controller = fields.Boolean(
        string="Validation controller", default=False,
        help="Start time of the order")
    booking_identifier = fields.Boolean(string="Booking Identifier",
                                        help="Field to identify booking")
    user_id = fields.Many2one('res.users', string="Chair User")
    salon_order_created_user = fields.Integer(string="Salon Order Created User",
                                              default=lambda self: self._uid,
                                              help="The user whom the salon"
                                                   " order created.")
    count = fields.Integer(string='Delivery Orders', compute='_compute_count',
                           help="The count of the delivery")

    @api.depends('order_line_ids.price_subtotal')
    def _compute_price_subtotal(self):
        """Compute the subtotal price of order line"""
        amount_untaxed = 0.0
        total_time_taken = 0.0
        for order in self:
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
                total_time_taken += line.time_taken
        self.price_subtotal = amount_untaxed
        time_takes = total_time_taken
        hours = int(time_takes)
        minutes = (time_takes - hours) * 60
        start_time_store = datetime.strptime(
            str(self.start_time).split(".")[0], "%Y-%m-%d %H:%M:%S")
        self.write({'end_time': start_time_store + timedelta(
            hours=hours, minutes=minutes),
                    'time_taken_total': total_time_taken})

    def _compute_count(self):
        """Compute invoice count of salon orders"""
        for orders in self:
            orders.count = self.env['account.move'].search_count(
                [('invoice_origin', '=', self.name)])

    def action_view_invoice_salon(self):
        """Function to open invoice for the salon order"""
        return {'name': 'Invoices',
                'domain': [('invoice_origin', '=', self.name)],
                'res_model': 'account.move',
                'view_id': False,
                'view_mode': 'tree,form',
                'type': 'ir.actions.act_window'}

    @api.model
    def _read_group_stage_ids(self, stages, domain, order):
        """Return the stages to stage_ids"""
        return self.env['salon.stage'].search([])

    def write(self, values):
        """ Manage drag and drop in salon order kanban view """
        if 'stage_id' in values.keys():
            if self.stage_id.id == 3:
                if values['stage_id'] != 4:
                    raise ValidationError(_("You can't perform that move!"))
                else:
                    time_taken_chair = self.chair_id.total_time_taken_chair
                    self.chair_id.total_time_taken_chair = (
                            time_taken_chair - self.time_taken_total)
            if self.stage_id.id == 4:
                raise ValidationError(
                    _("You can't move a salon order from Closed stage!"))
            if self.stage_id.id == 5:
                raise ValidationError(
                    _("You can't move a salon order from Cancel stage!"))
            if self.stage_id.id == 1:
                if values['stage_id'] not in [2, 5]:
                    raise ValidationError(_("You can't perform that move!"))
            if self.stage_id.id == 2:
                if values['stage_id'] == 5:
                    time_taken_chair = self.chair_id.total_time_taken_chair
                    self.chair_id.total_time_taken_chair = (
                            time_taken_chair - self.time_taken_total)
                elif values['stage_id'] == 1 or values['stage_id'] == 4:
                    raise ValidationError(_("You can't perform that move!"))
                elif values['stage_id'] == 3 and not self.inv_stage_identifier:
                    self.action_create_invoice()
        if 'stage_id' in values.keys() and self.name == "Draft Salon Order":
            if values['stage_id'] == 2:
                self.action_validate()
                self.action_confirm()
        self.update_number_of_orders()
        return super(SalonOrder, self).write(values)

    def action_confirm(self):
        """Confirm function of salon order"""
        sequence_code = 'salon.order.sequence'
        order_date = str(self.date)
        order_date = order_date[0:10]
        self.name = self.env['ir.sequence'].with_context(
            ir_sequence_date=order_date).next_by_code(sequence_code)
        if self.partner_id:
            self.partner_id.partner_salon = True
        self.stage_id = 2
        self.update_number_of_orders()
        self.chair_id.total_time_taken_chair += self.time_taken_total
        self.user_id = self.chair_id.user_id

    def action_validate(self):
        """ Validate function of salon order"""
        self.validation_controller = True
        self.update_number_of_orders()

    def action_close(self):
        """Close function for salon order"""
        self.stage_id = 4
        self.update_number_of_orders()

    def action_cancel(self):
        """Function to cancel the salon order"""
        self.stage_id = 5
        self.update_number_of_orders()

    def action_update_total(self):
        """Update total amount in salon order"""
        for order in self:
            amount_untaxed = 0.0
            for line in order.order_line_ids:
                amount_untaxed += line.price_subtotal
            order.price_subtotal = amount_untaxed

    @api.onchange('chair_id')
    def _onchange_chair_id(self):
        """Onchange function of chair_id field"""
        if 'active_id' in self._context.keys():
            self.chair_id = self._context['active_id']

    def action_create_invoice(self):
        """Function to create invoice"""
        if self.partner_id:
            supplier = self.partner_id
        else:
            supplier = self.partner_id.search(
                [("name", "=", "Salon Default Customer")])
        lines = []
        product_id = self.env['product.product'].search(
            [("name", "=", "Salon Service")])
        for records in self.order_line_ids:
            if product_id.property_account_income_id.id:
                income_account = product_id.property_account_income_id.id
            elif product_id.categ_id.property_account_income_categ_id.id:
                income_account = product_id.categ_id. \
                    property_account_income_categ_id.id
            else:
                raise UserError(
                    _("Please define income account for this product: "
                      "'%s' (id:%d).") % (product_id.name, product_id.id))
            value = (0, 0, {
                'name': records.service_id.name,
                'account_id': income_account,
                'price_unit': records.price,
                'quantity': 1,
                'product_id': product_id.id,
            })
            lines.append(value)
        result = {
            'name': self.env.ref('account.action_move_out_invoice_type',
                                 raise_if_not_found=False).name,
            'type': 'ir.actions.act_window',
            'views': [[False, 'form']],
            'target': 'current',
            'res_id': self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': supplier.id,
                'invoice_user_id': self.env.user.id,
                'invoice_origin': self.name,
                'invoice_line_ids': lines}).id,
            'res_model': 'account.move',
        }
        self.inv_stage_identifier = True
        self.stage_id = 3
        invoiced_records = self.env['salon.order'].search(
            [('stage_id', 'in', [3, 4]), ('chair_id', '=', self.chair_id.id)])
        total = 0
        for rows in invoiced_records:
            invoiced_date = str(rows.date)
            invoiced_date = invoiced_date[0:10]
            if invoiced_date == str(date.today()):
                total = total + rows.price_subtotal
        self.chair_id.collection_today = total
        self.update_number_of_orders()
        return result

    def unlink(self):
        """ Unlink/delete salon order """
        for order in self:
            if order.stage_id.id == 3 or order.stage_id.id == 4:
                raise UserError(_("You can't delete an invoiced salon order!"))
        return super(SalonOrder, self).unlink()

    def update_number_of_orders(self):
        """ Function to update the number of active orders for the chair."""
        self.chair_id.number_of_orders = len(self.env['salon.order'].search([
        ]).filtered(lambda order: order.chair_id.id == self.chair_id.id
                    and order.stage_id in [2, 3]))
