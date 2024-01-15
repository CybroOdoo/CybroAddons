# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta
from odoo import api, fields, models


class SaleRecurring(models.Model):
    """Helps to create a recurring sale order"""
    _name = 'sale.recurring'
    _description = 'Sale Order Recurring'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name", readonly=True, copy=False, default='New',
                       help="Sequence of recurring order")
    title = fields.Char(string='Title', help="Name of the order")
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 required=True,
                                 help="Customer name")
    start_date = fields.Date(string='Start Date', required=True,
                             help=" Start the sale order creation based on the"
                                  " start date")
    stop_after = fields.Integer(string='Stop After',
                                help='Total days to end the sale order'
                                     ' creation')
    end_date = fields.Date(string='End Date', readonly=True,
                           help='Stop the sale order creation based on '
                                'the end date', tracking=True)
    state = fields.Selection(selection=[('running', 'Running'),
                                        ('expired', 'Expired'),
                                        ('cancelled', 'Cancelled')],
                             string='Status', copy=False, default='running',
                             help='State of recurring order', tracking=True)
    total_sale_order = fields.Integer(string="Total SO",
                                      compute='_compute_total_sale_order',
                                      help='Count of total sale orders')
    total_sale_quotation = fields.Integer(
        string="Total RFQ",
        compute='_compute_total_sale_quotation',
        help='Count of total quotations')
    active = fields.Boolean(default=True, string='Active',
                            help='If unchecked, it will allow you to hide the'
                                 ' recurring order without removing it.',
                            tracking=True)
    order_line_ids = fields.One2many('sale.recurring.line', 'order_id',
                                     string="Order lines",
                                     help='To store recurring order datas')

    @api.model
    def create(self, vals):
        """Sequence creation of recurring order."""
        vals['name'] = self.env['ir.sequence'].next_by_code('sequence.order')
        return super(SaleRecurring, self).create(vals)

    @api.onchange('stop_after', 'start_date')
    def _onchange_start_date(self):
        """Update end date based on the start_date and stop_after"""
        self.end_date = 0
        if self.stop_after > 0:
            self.end_date = self.start_date + timedelta(days=self.stop_after)

    def action_create_sale_order(self):
        """Create sale order from the created sale recurring"""
        line_vals = [fields.Command.create({'product_id': rec.product_id.id,
                                            'product_uom_qty': rec.product_uom_qty,
                                            'price_unit': rec.price_unit,
                                            'name': rec.name}) for rec in
                     self.order_line_ids]
        if line_vals:
            self.env['sale.order'].sudo().create({
                'partner_id': self.partner_id.id,
                'recurring_order_id': self.id,
                'order_line': line_vals
            })

    def action_cancel_recurring_order(self):
        """Cancel recurring orders if not necessary"""
        self.state = 'cancelled'

    def action_renew(self):
        """Renew the recurring order if they are cancelled."""
        self.state = 'running'

    def cron_sale_order_creation(self):
        """Create sale orders automatically while checking the conditions
         of start date and end date"""
        recurring_data = self.env['sale.recurring'].search([])
        for rec in recurring_data:
            if rec.end_date and rec.end_date < fields.Date.today():
                rec.state = 'expired'
            if rec.state == 'running':
                if rec.end_date and rec.start_date <= fields.Date.today() <= rec.end_date:
                    rec.action_create_sale_order()
                elif rec.start_date <= fields.Date.today():
                    rec.action_create_sale_order()

    def action_get_sale_orders(self):
        """Get total sale orders in sale recurring smart button"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'reservation',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('recurring_order_id', '=', self.id),
                       ('state', '=', 'sale')],
        }

    def action_get_sale_quotations(self):
        """Get total sale quotations in sale recurring smart button"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'reservation',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'domain': [('recurring_order_id', '=', self.id),
                       ('state', 'in', ['draft', 'sent'])],
        }

    def _compute_total_sale_order(self):
        """Compute total number of sale orders"""
        for record in self:
            record.total_sale_order = self.env[
                'sale.order'].search_count(
                [('recurring_order_id', '=', record.id),
                 ('state', '=', 'sale')])

    def _compute_total_sale_quotation(self):
        """Compute total number of quotations."""
        for record in self:
            record.total_sale_quotation = self.env[
                'sale.order'].search_count(
                [('recurring_order_id', '=', record.id),
                 ('state', 'in', ['draft', 'sent'])])

    def action_archive_orders(self):
        """Archive recurring orders"""
        self.active = False

    def action_unarchive_orders(self):
        """Un archive recurring orders"""
        self.active = True
