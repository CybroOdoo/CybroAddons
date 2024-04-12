# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: JANISH BABU (<https://www.cybrosys.com>)
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
#############################################################################
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError


class SubscriptionPackage(models.Model):
    """Subscription Package Model"""
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
                       store=True, required=True,
                       help='Choose the name for the subscription package.')
    partner_id = fields.Many2one('res.partner', string='Customer',
                                 help='Select the customer associated with this record.')
    partner_invoice_id = fields.Many2one('res.partner',
                                         help='Select the invoice address '
                                              'associated with this record.',
                                         string='Invoice Address',
                                         related='partner_id')
    partner_shipping_id = fields.Many2one('res.partner',
                                          help="Add shipping/service address",
                                          string='Shipping/Service Address',
                                          related='partner_id')
    plan_id = fields.Many2one('subscription.package.plan',
                              string='Subscription Plan',
                              help="Choose the subscription package plan")
    start_date = fields.Date(string='Period Start Date',
                             help='Add the period start date',
                             ondelete='restrict')
    date_started = fields.Date(string='Subsciption Start date',
                               help='Add the Subscription package start date',
                               ondelete='restrict', readonly=True)
    next_invoice_date = fields.Date(string='Next Invoice Date',
                                    store=True, help='Add next invoice date',
                                    compute="_compute_next_invoice_date")
    company_id = fields.Many2one('res.company', string='Company',
                                 help='Select the company',
                                 default=lambda self: self.env.company,
                                 required=True)
    user_id = fields.Many2one('res.users', string='Sales Person',
                              help='Add the Sales person',
                              default=lambda self: self.env.user)
    sale_order_id = fields.Many2one('sale.order', string="Sale Order",
                                    help='Select the sale order', copy=False)
    is_to_renew = fields.Boolean(string='To Renew', copy=True,
                                 help='Is subscription package is renew')
    tag_ids = fields.Many2many('account.account.tag', string='Tags',
                               help='Add the tags')
    stage_id = fields.Many2one('subscription.package.stage', string='Stage',
                               default=lambda self: self._default_stage_id(),
                               index=True,
                               group_expand='_read_group_stage_ids',
                               help='Subscription Package stage', copy=False)
    invoice_count = fields.Integer(string='Invoices',
                                   help='Subscription package invoice count',
                                   compute='_compute_invoice_count')
    so_count = fields.Integer(string='Sales',
                              help='subscription package sales count',
                              compute='_compute_sale_count')
    description = fields.Text(string='Description',
                              help='Subscription package description')
    analytic_account_id = fields.Many2one('account.analytic.account',
                                          help='Choose the analytic account',
                                          string='Analytic Account')
    product_line_ids = fields.One2many('subscription.package.product.line',
                                       'subscription_id', ondelete='restrict',
                                       string='Products Line',
                                       help='Subscription package product line')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True, default=lambda
            self: self.env.company.currency_id, help='Add Currency')
    current_stage = fields.Char(string='Current Stage', default='Draft',
                                help='Current stage of the '
                                     'subscription package. '
                                     'This field is computed based on '
                                     'the associated stage_id.',
                                store=True, compute='_compute_current_stage')
    reference_code = fields.Char(string='Reference',
                                 help='This field represents the '
                                      'reference code associated '
                                      'with the record.')
    is_closed = fields.Boolean(string="Closed", default=False,
                               help='Is Closed')
    close_reason_id = fields.Many2one('subscription.package.stop',
                                      help='The reason for c'
                                           'losing the subscription package.',
                                      string='Close Reason')
    closed_by = fields.Many2one('res.users', string='Closed By',
                                help="The user responsible "
                                     "for closing the record")
    close_date = fields.Date(string='Closed on',
                             help="The date on which the record was closed")
    stage_category = fields.Selection(related='stage_id.category',
                                      help="The category associated with "
                                           "the current stage of the record. ",
                                      store=True)
    invoice_mode = fields.Selection(related="plan_id.invoice_mode",
                                    help="The invoice mode "
                                         "associated with the plan.")
    total_recurring_price = fields.Float(string='Untaxed Amount',
                                         help="The total recurring "
                                              "price excluding taxes.",
                                         compute='_compute_total_recurring_price',
                                         store=True)
    tax_total = fields.Float("Taxes", readonly=True,
                             help="The total amount of "
                                  "taxes associated with the record")
    total_with_tax = fields.Monetary("Total Recurring Price", readonly=True,
                                     help="The total recurring "
                                          "price including taxes")
    recurrence_period_id = fields.Many2one("recurrence.period",
                                           string="Recurrence Period")
    sale_order_count = fields.Integer(string='Sale Order Count',
                                      help="The count of associated "
                                           "sale orders for this record.")

    def _valid_field_parameter(self, field, name):
        """Check the validity of a field parameter for a specific field."""
        if name == 'ondelete':
            return True
        return super(SubscriptionPackage,
                     self)._valid_field_parameter(field, name)

    @api.depends('invoice_count')
    def _compute_invoice_count(self):
        """ Calculate Invoice count based on subscription package """
        sale_id = self.env['sale.order'].search(
            [('id', '=', self.sale_order_id.id)])
        invoices = sale_id.order_line.invoice_lines.move_id.filtered(
            lambda r: r.move_type in ('out_invoice', 'out_refund'))
        invoices.write({'subscription_id': self.id})
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
            [('id', '=', self.sale_order_id.id)])

    @api.depends('stage_id')
    def _compute_current_stage(self):
        """ It displays current stage for subscription package """
        for rec in self:
            rec.current_stage = rec.env['subscription.package.stage'].search(
                [('id', '=', rec.stage_id.id)]).category

    @api.constrains('start_date')
    def _compute_next_invoice_date(self):
        """The compute function is the next invoice date for subscription
        packages based on the start date and renewal time."""
        for sub in self.env['subscription.package'].search([]):
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
            'domain': [('id', '=', self.sale_order_id.id)],
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
            'res_model': 'subscription.close',
            'target': 'new'
        }

    def button_start_date(self):
        """Button to start subscription package"""
        stage_id = (self.env['subscription.package.stage'].search([
            ('category', '=', 'progress')], limit=1).id)
        for rec in self:
            if len(rec.env['subscription.package.stage'].search(
                    [('category', '=', 'draft')])) > 1:
                raise UserError(
                    _('More than one stage is having category "Draft". '
                      'Please change category of stage to "In Progress", '
                      'only one stage is allowed to have category "Draft"'))
            else:
                if not rec.product_line_ids:
                    raise UserError("Empty order lines !! Please add the "
                                    "subscription product.")
                else:
                    rec.write(
                        {'stage_id': stage_id,
                         'date_started': fields.Date.today(),
                         'start_date': fields.Date.today()})

    def button_sale_order(self):
        """Button to create sale order"""
        this_products_line = []
        for rec in self.product_line_ids:
            rec_list = [0, 0, {'product_id': rec.product_id.id,
                               'product_uom_qty': rec.product_qty,
                               'discount': rec.discount}]
            this_products_line.append(rec_list)
        orders = self.env['sale.order'].search(
            [('id', '=', self.sale_order_count),
             ('invoice_status', '=', 'no')])
        if orders:
            for order in orders:
                order.action_confirm()
        so_id = self.env['sale.order'].create({
            'id': self.sale_order_count,
            'partner_id': self.partner_id.id,
            'partner_invoice_id': self.partner_id.id,
            'partner_shipping_id': self.partner_id.id,
            'is_subscription': True,
            'subscription_id': self.id,
            'order_line': this_products_line
        })
        self.sale_order_id = so_id
        return {
            'name': _('Sales Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'domain': [('id', '=', so_id.id)],
            'view_mode': 'tree,form',
            'context': {
                "create": False
            }
        }

    @api.model_create_multi
    def create(self, vals_list):
        """It displays subscription product in partner and generate sequence"""
        for vals in vals_list:
            partner = self.env['res.partner'].search(
                [('id', '=', vals.get('partner_id'))])
            partner.is_active_subscription = True
            if vals.get('reference_code', 'New') is False:
                vals['reference_code'] = self.env['ir.sequence'].next_by_code(
                    'sequence.reference.code') or 'New'
            create_id = super().create(vals)
            return create_id

    @api.depends('reference_code')
    def _compute_name(self):
        """It displays record name as combination of short code, reference
        code and partner name """
        for rec in self:
            plan_id = self.env['subscription.package.plan'].search(
                [('id', '=', rec.plan_id.id)])
            if plan_id.short_code and rec.reference_code:
                rec.name = plan_id.short_code + '/' + rec.reference_code + '-' + rec.partner_id.name

    def set_close(self):
        """ Button to close subscription package """
        stage = self.env['subscription.package.stage'].search(
            [('category', '=', 'closed')], limit=1).id
        for sub in self:
            values = {'stage_id': stage, 'is_to_renew': False}
            sub.write(values)
        return True

    def send_renew_alert_mail(self, today, renew_date, sub_id):
        """The function is used to send a renewal alert email and mark the
        subscription for renewal if today is the renewal date."""
        if today == renew_date:
            self.env.ref(
                'subscription_package'
                '.mail_template_subscription_renew').send_mail(
                sub_id, force_send=True)
            subscription = self.env['subscription.package'].browse(sub_id)
            subscription.write({'is_to_renew': True})
            return True
        else:
            return False

    def find_renew_date(self, next_invoice, date_started, end):
        """The function is used to calculate the renewal date, end date,
        and close date based on subscription details."""
        if end == 0:
            end_date = next_invoice
            difference = (next_invoice - date_started).days / 10
            renew_date = next_invoice - relativedelta(
                days=difference)
            close_date = next_invoice
        else:
            end_date = fields.Date.add(date_started,
                                       days=end)
            close = date_started + relativedelta(days=end)
            difference = (close - date_started).days / 10
            renew_date = close - relativedelta(
                days=difference)
            close_date = close

        data = {'renew_date': renew_date,
                'end_date': end_date,
                'close_date': close_date}
        return data

    def close_limit_cron(self):
        """ It Checks renew date, close date. It will send mail when renew
        date and also generates invoices based on the plan.
        It wil close the subscription automatically if renewal limit is exceeded """
        pending_subscriptions = self.env['subscription.package'].search(
            [('stage_category', '=', 'progress')])
        today_date = fields.Date.today()
        # today_date = datetime.datetime.strptime('05102023', '%d%m%Y').date()
        pending_subscription = False
        for pending_subscription in pending_subscriptions:
            get_dates = self.find_renew_date(
                pending_subscription.next_invoice_date,
                pending_subscription.date_started,
                pending_subscription.plan_id.days_to_end)
            renew_date = get_dates['renew_date']
            end_date = get_dates['end_date']
            pending_subscription.close_date = get_dates['close_date']
            if today_date == pending_subscription.next_invoice_date:
                if pending_subscription.plan_id.invoice_mode == 'draft_invoice':
                    this_products_line = []
                    for rec in pending_subscription.product_line_ids:
                        rec_list = [0, 0, {'product_id': rec.product_id.id,
                                           'quantity': rec.product_qty,
                                           'price_unit': rec.unit_price,
                                           'discount': rec.discount,
                                           'tax_ids': rec.tax_ids
                                           }]
                        this_products_line.append(rec_list)
                    self.env['account.move'].create(
                        {
                            'move_type': 'out_invoice',
                            'invoice_date_due': today_date,
                            'invoice_payment_term_id': False,
                            'invoice_date': today_date,
                            'state': 'draft',
                            'subscription_id': pending_subscription.id,
                            'partner_id': pending_subscription.partner_invoice_id.id,
                            'currency_id': pending_subscription.partner_invoice_id.currency_id.id,
                            'invoice_line_ids': this_products_line
                        })

                    pending_subscription.write({'is_to_renew': False,
                                                'start_date': pending_subscription.next_invoice_date})
                    new_date = self.find_renew_date(
                        pending_subscription.next_invoice_date,
                        pending_subscription.date_started,
                        pending_subscription.plan_id.days_to_end)
                    pending_subscription.write(
                        {'close_date': new_date['close_date']})
                    self.send_renew_alert_mail(today_date,
                                               new_date['renew_date'],
                                               pending_subscription.id)

            if (today_date == end_date) and (
                    pending_subscription.plan_id.limit_choice != 'manual'):
                display_msg = ("<h5><i>The renewal limit has been exceeded "
                               "today for this subscription based on the "
                               "current subscription plan.</i></h5>")
                pending_subscription.message_post(body=display_msg)
                pending_subscription.is_closed = True
                reason = (self.env['subscription.package.stop'].search([
                    ('name', '=', 'Renewal Limit Exceeded')]).id)
                pending_subscription.close_reason_id = reason
                pending_subscription.closed_by = self.user_id
                pending_subscription.close_date = fields.Date.today()
                stage = (self.env['subscription.package.stage'].search([
                    ('category', '=', 'closed')]).id)
                values = {'stage_id': stage, 'is_to_renew': False,
                          'next_invoice_date': False}
                pending_subscription.write(values)

            self.send_renew_alert_mail(today_date, renew_date,
                                       pending_subscription.id)

        return dict(pending=pending_subscription)

    @api.depends('product_line_ids.total_amount',
                 'product_line_ids.price_total', 'product_line_ids.tax_ids')
    def _compute_total_recurring_price(self):
        """ The compute function used to calculate recurring price """
        for record in self:
            total_recurring = 0
            total_tax = 0.0
            for line in record.product_line_ids:
                if line.total_amount != line.price_total:
                    line_tax = line.price_total - line.total_amount
                    total_tax += line_tax

                total_recurring += line.total_amount
            record['total_recurring_price'] = total_recurring
            record['tax_total'] = total_tax
            total_with_tax = total_recurring + total_tax
            record['total_with_tax'] = total_with_tax

    def action_renew(self):
        """ The function is used to perform the renewal
        action for the subscription package."""
        return self.button_sale_order()
