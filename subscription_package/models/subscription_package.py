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

from odoo import _, api, models, fields, SUPERUSER_ID
import datetime
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class SubscriptionPackageProductLine(models.Model):
    _name = 'subscription.package.product.line'
    _description = 'Subscription Product Lines'

    subscription_id = fields.Many2one('subscription.package', store=True,
                                      string='Subscription')
    company_id = fields.Many2one('res.company', string='Company', store=True,
                                 related='subscription_id.company_id')
    create_date = fields.Datetime(string='Create date', store=True,
                                  default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='Salesperson', store=True,
                              related='subscription_id.user_id')
    product_id = fields.Many2one('product.product', string='Product',
                                 store=True, ondelete='restrict',
                                 domain=[('is_subscription', '=', True)])
    product_qty = fields.Float(string='Quantity', store=True, default=1.0)
    product_uom_id = fields.Many2one('uom.uom', string='UoM', store=True,
                                     related='product_id.uom_id',
                                     ondelete='restrict')
    uom_catg_id = fields.Many2one('uom.category', string='UoM', store=True,
                                  related='product_id.uom_id.category_id')
    unit_price = fields.Float(string='Unit Price', store=True, readonly=False,
                              related='product_id.list_price')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  store=True,
                                  related='subscription_id.currency_id')
    total_amount = fields.Monetary(string='Subtotal', store=True,
                                   compute='_compute_total_amount')
    sequence = fields.Integer('Sequence', help="Determine the display order",
                              index=True)
    res_partner_id = fields.Many2one('res.partner', string='Currency',
                                     store=True,
                                     related='subscription_id.partner_id')

    @api.depends('product_qty', 'unit_price')
    def _compute_total_amount(self):
        """ Calculate subtotal amount of product line """
        for rec in self:
            if rec.product_id:
                rec.total_amount = rec.unit_price * rec.product_qty


class SubscriptionPackage(models.Model):
    _name = 'subscription.package'
    _description = 'Subscription Package'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model
    def _read_group_stage_ids(self, categories, domain, order):
        """ Read all the stages and display it in the kanban view,
            even if it is empty."""
        category_ids = categories._search([], order=order,
                                          access_rights_uid=SUPERUSER_ID)
        return categories.browse(category_ids)

    def _default_stage_id(self):
        """Setting default stage"""
        rec = self.env['subscription.package.stage'].search([], limit=1,
                                                            order='sequence ASC')
        return rec.id if rec else None

    name = fields.Char(string='Name', default="New", compute='_compute_name',
                       store=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer', store=True)
    partner_invoice_id = fields.Many2one('res.partner',
                                         string='Invoice Address',
                                         related='partner_id', readonly=False)
    partner_shipping_id = fields.Many2one('res.partner',
                                          string='Shipping/Service Address',
                                          related='partner_id',
                                          readonly=False)
    plan_id = fields.Many2one('subscription.package.plan',
                              string='Subscription Plan')
    start_date = fields.Date(string='Start Date', store=True,
                             ondelete='restrict')
    next_invoice_date = fields.Date(string='Next Invoice Date', readonly=False,
                                    store=True,
                                    compute="_compute_next_invoice_date")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company,
                                 required=True)
    user_id = fields.Many2one('res.users', string='Sales Person',
                              default=lambda self: self.env.user)
    sale_order = fields.Many2one('sale.order', string="Sale Order")
    to_renew = fields.Boolean(string='To Renew', default=False)
    tag_ids = fields.Many2many('account.analytic.tag', string='Tags')
    stage_id = fields.Many2one('subscription.package.stage', string='Stage',
                               default=lambda self: self._default_stage_id(),
                               index=True,
                               group_expand='_read_group_stage_ids')
    invoice_count = fields.Integer(string='Invoices',
                                   compute='_compute_invoice_count')
    so_count = fields.Integer(string='Sales', compute='_compute_sale_count')
    description = fields.Text(string='Description')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          string='Analytic Account')
    product_line_ids = fields.One2many('subscription.package.product.line',
                                       'subscription_id', ondelete='restrict',
                                       string='Products Line')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True,
                                  default=lambda
                                      self: self.env.company.currency_id)
    current_stage = fields.Char(string='Current Stage', default='Draft',
                                store=True, compute='_compute_current_stage')
    reference_code = fields.Char(string='Reference', store=True)
    is_closed = fields.Boolean(string="Closed", default=False)
    close_reason = fields.Many2one('subscription.package.stop',
                                   string='Close Reason')
    closed_by = fields.Many2one('res.users', string='Closed By')
    close_date = fields.Date(string='Closed on')
    stage_category = fields.Selection(related='stage_id.category', store=True)
    invoice_mode = fields.Selection(related="plan_id.invoice_mode")
    total_recurring_price = fields.Float(string='Recurring Price',
                                         compute='_compute_total_recurring_price',
                                         store=True)

    @api.depends('invoice_count')
    def _compute_invoice_count(self):
        """ Calculate Invoice count based on subscription package """
        invoice_count = self.env['account.move'].search_count(
            [('subscription_id', '=', self.id)])
        if invoice_count > 0:
            self.invoice_count = invoice_count
        else:
            self.invoice_count = 0

    @api.depends('so_count')
    def _compute_sale_count(self):
        """ Calculate sale order count based on subscription package """
        self.so_count = self.env['sale.order'].search_count(
            [('subscription_id', '=', self.id)])

    @api.depends('stage_id')
    def _compute_current_stage(self):
        """ It displays current stage for subscription package """
        for rec in self:
            rec.current_stage = rec.env['subscription.package.stage'].search(
                [('id', '=', rec.stage_id.id)]).category

    @api.depends('start_date')
    def _compute_next_invoice_date(self):
        pending_subscriptions = self.env['subscription.package'].search(
            [('stage_category', '=', 'progress')])
        for sub in pending_subscriptions:
            if sub.start_date:
                sub.next_invoice_date = sub.start_date + relativedelta(
                    days=sub.plan_id.renewal_time)

    def button_invoice_count(self):
        """ It displays invoice based on subscription package """
        return {
            'name': 'Invoices',
            'domain': [('subscription_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def button_sale_count(self):
        """ It displays sale order based on subscription package """
        return {
            'name': 'Products',
            'domain': [('subscription_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def button_close(self):
        """ Button for subscription close wizard """
        return {
            'name': "Subscription Close Reason",
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'subscription.close.wizard',
            'target': 'new'
        }

    def button_payment(self):
        """ Button to create invoice for subscription package"""
        this_products_line = []
        for rec in self.product_line_ids:
            rec_list = [0, 0, {'product_id': rec.product_id.id,
                               'quantity': rec.product_qty}]
            this_products_line.append(rec_list)
        invoices = self.env['account.move'].search([('subscription_id', '=', self.id), ('state', '=', 'draft')])
        orders = self.env['sale.order'].search([('subscription_id', '=', self.id), ('invoice_status', '=', 'no')])
        if invoices:
            for invoice in invoices:
                invoice.action_post()
        if orders and invoices:
            for order in orders:
                order.action_confirm()
            for invoice in invoices:
                invoice.action_post()
        out_invoice = self.env['account.move'].create(
            {
                'move_type': 'out_invoice',
                'date': fields.Date.today(),
                'invoice_date': fields.Date.today(),
                'partner_id': self.partner_invoice_id.id,
                'currency_id': self.partner_invoice_id.currency_id.id,
                'invoice_line_ids': this_products_line
            })
        self.env['account.move'].payment_id = out_invoice.id
        if self.stage_category == 'progress':
            values = {'start_date': datetime.datetime.today()}
            self.write(values)
        return {
            'name': 'Subscription Payment',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': out_invoice.id
        }

    def button_start_date(self):
        """Button to start subscription package"""
        if not self.start_date:
            self.start_date = datetime.date.today()
            for rec in self:
                if len(rec.env['subscription.package.stage'].search([('category', '=', 'draft')])) > 1:
                    raise UserError(
                        _('More than one stage is having category "Draft". '
                          'Please change category of stage to "In Progress", '
                          'only one stage is allowed to have category "Draft"'))
                else:
                    rec.write(
                        {'stage_id': (rec.env['subscription.package.stage'].search([
                            ('category', '=', 'draft')]).id) + 1})

    def button_sale_order(self):
        """Button to create sale order"""
        this_products_line = []
        for rec in self.product_line_ids:
            rec_list = [0, 0, {'product_id': rec.product_id.id,
                               'product_uom_qty': rec.product_qty}]
            this_products_line.append(rec_list)
        # for order in self.sale_order:
        orders = self.env['sale.order'].search([('subscription_id', '=', self.id), ('invoice_status', '=', 'no')])
        if orders:
            for order in orders:
                order.action_confirm()
        so_id = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'is_subscription': True,
            'subscription_id': self.id,
            'order_line': this_products_line
        })
        self.sale_order = so_id
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('id', '=', so_id.id)],
            'view_mode': 'tree,form'
        }

    @api.model
    def create(self, vals):
        """It displays subscription product in partner and generate sequence"""
        partner = self.env['res.partner'].search(
            [('id', '=', vals.get('partner_id'))])
        partner.active_subscription = True
        if vals.get('reference_code', 'New') is False:
            vals['reference_code'] = self.env['ir.sequence'].next_by_code(
                'sequence.reference.code') or 'New'
        create_id = super(SubscriptionPackage, self).create(vals)
        return create_id

    @api.depends('reference_code')
    def _compute_name(self):
        """It displays record name as combination of short code, reference
        code and partner name """
        plan_id = self.env['subscription.package.plan'].search(
            [('id', '=', self.plan_id.id)])
        if plan_id.short_code and self.reference_code:
            self.name = plan_id.short_code + '/' + self.reference_code + '-' + self.partner_id.name

    def set_close(self):
        """ Button to close subscription package """
        stage = self.env['subscription.package.stage'].search(
            [('category', '=', 'closed')], limit=1).id
        for sub in self:
            values = {'stage_id': stage, 'to_renew': False}
            sub.write(values)
        return True

    def close_limit_cron(self):
        """ It Checks renew date, close date. It will send mail when renew date """
        pending_subscriptions = self.env['subscription.package'].search(
            [('stage_category', '=', 'progress')])
        today_date = fields.Date.today()
        pending_subscription = False
        close_subscription = False
        for pending_subscription in pending_subscriptions:
            pending_subscription.close_date = pending_subscription.start_date + relativedelta(
                days=pending_subscription.plan_id.days_to_end)
            difference = (
                                 pending_subscription.close_date - pending_subscription.start_date).days / 10
            renew_date = pending_subscription.close_date - relativedelta(
                days=difference)
            if today_date == renew_date:
                self.env.ref(
                    'subscription_package.mail_template_subscription_renew').send_mail(
                    pending_subscription.id, force_send=True)
                pending_subscription.write({'to_renew': True})
                if pending_subscription.plan_id.invoice_mode == 'draft_invoice':
                    this_products_line = []
                    for rec in pending_subscription.product_line_ids:
                        rec_list = [0, 0, {'product_id': rec.product_id.id,
                                           'quantity': rec.product_qty}]
                        this_products_line.append(rec_list)
                        self.env['account.move'].create(
                            {
                                'move_type': 'out_invoice',
                                'date': fields.Date.today(),
                                'invoice_date': fields.Date.today(),
                                'state': 'draft',
                                'partner_id': pending_subscription.partner_invoice_id.id,
                                'currency_id': pending_subscription.partner_invoice_id.currency_id.id,
                                'invoice_line_ids': this_products_line
                            })
                    pending_subscription.write({'to_renew': False,
                                                'start_date': datetime.datetime.today()})
        close_subscriptions = self.env['subscription.package'].search(
            [('stage_category', '=', 'progress'), ('to_renew', '=', True)])
        for close_subscription in close_subscriptions:
            close_subscription.close_date = close_subscription.start_date + relativedelta(
                days=close_subscription.plan_id.days_to_end)
            if today_date == close_subscription.close_date:
                close_subscription.set_close()
        return dict(pending=pending_subscription, closed=close_subscription)

    @api.depends('product_line_ids.total_amount')
    def _compute_total_recurring_price(self):
        """ Calculate recurring price """
        for record in self:
            total_recurring = 0
            for line in record.product_line_ids:
                total_recurring += line.total_amount
            record['total_recurring_price'] = total_recurring

    def action_renew(self):
        return self.button_sale_order()
