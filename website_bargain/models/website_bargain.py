# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import logging
from datetime import timedelta
from odoo import api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class WebsiteBargain(models.Model):
    """This is the main class of website bargain where all the details are
        stored in this model
        _onchange_template_id:
            function for automatically add the auction name
        _check_end_date:
            function to validate the end date if it is higher than the start
            date
        _check_extend_time:
            function to validate extended time whether it is greater than end
            time and after saving will send notification to subscribers if
            enabled
        action_confirm:
            button function to confirm auction and will make product as
            published
        action_reset_to_draft:
            button function to reset the auction to draft
        action_run_auction:
            button function to start auction manually
        action_complete:
            button function to end auction manually
        action_close:
            button function to close auction
        send_email_notification:
                Function for sending auction notification for admin
                 before ending if enabled
        auction_auto_start:
                Cron function for auction auto start when its start
                time and also will send notification to customers about auction
    """
    _name = 'website.bargain'
    _description = "Website Bargain"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    website_id = fields.Many2one('website', string='Website', required=True,
                                 help="Add website here to put auction")
    template_id = fields.Many2one('bargain.template', string='Template',
                                  help="add already created templates of "
                                       "auction with products")
    auction_manager_id = fields.Many2one('res.users', string="Auction Manager",
                                         help="Set auction manager here",
                                         required=True)
    product_id = fields.Many2one(related='template_id.product_id', store=True,
                                 string='Product', readonly=False,
                                 help="Select the product", required=True)
    name = fields.Char(string='Auction Name', help="Auctions name")
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda
                                      self: self.env.company.currency_id.id,
                                  required=True,
                                  help="if you select this "
                                       "currency bidding will "
                                       "be on that currency itself")
    initial_price = fields.Monetary(string='Initial Price',
                                    currency_field='currency_id',
                                    required=True,
                                    help="Minimum amount required to bid")
    is_buy_now = fields.Boolean(string='Provide buy now button',
                                help='Enable a button for buying instantly')
    price_buy_now = fields.Monetary(string='Buy Now Price',
                                    currency_field='currency_id',
                                    help="Price of the product if buying immediately")
    start_time = fields.Datetime(string='Start Date Time', required=True,
                                 default=fields.Datetime.now,
                                 help="Auction start time")
    end_time = fields.Datetime(string='End Date Time', required=True,
                               help="Auction end time")
    extend_time = fields.Datetime(string="Extended Time",
                                  help="By setting days you can "
                                       "extend the auction")
    state = fields.Selection(
        [('draft', "Draft"), ('confirmed', "Confirmed"),
         ('running', "Running"),
         ('closed', "Closed"), ('finished', "Finished")], default='draft')
    bargain_information_ids = fields.One2many('bargain.information',
                                              'auction_id', readonly=True)
    bargain_subscribers_ids = fields.One2many('bargain.subscribers',
                                              'auction_id')
    is_activate = fields.Boolean(string='Activate',
                                 help='this will activate '
                                      'notification for the admins')
    notify_on = fields.Integer(string='Notify before', default=5,
                               help="Set notification time here")
    notify_selection = fields.Selection(
        [('days', "Days"), ('hours', "Hours"), ('minutes', "Minutes"),
         ('seconds', "Seconds")], default='minutes')
    is_notification_send = fields.Boolean(string='Notification Send',
                                          help='If notification is sent manually, '
                                               'enable this field to restrict '
                                               'sending notification before '
                                               'the specified time')
    is_winner_notification = fields.Boolean(
        string='Send Notification to Winner',
        help='Enable this option to send notification to the winner')
    is_loser_notification = fields.Boolean(string='Send Notification to Loser',
                                           help='Enable this option to send '
                                                'notification to the losers')
    is_subscriber_start_notification = fields.Boolean(string='Bidding Start',
                                                      help="Send subscribers "
                                                           "the bidding start "
                                                           "notification")
    is_send_mail = fields.Boolean(string='Bidding Started Mail Sent',
                                  help='If Bidding mail has been sent to customer')
    is_extend_auction_notification = fields.Boolean(string='Auction Extended',
                                                    help="Send subscribers the "
                                                         "bidding extended "
                                                         "notification")
    is_new_bid_notification = fields.Boolean(string='New Bid Placed',
                                             help="Send subscribers "
                                                  "notifications if new bids"
                                                  " are placed")
    is_bid_end_notification = fields.Boolean(string='Auction Finished',
                                             help="Send subscribers "
                                                  "notifications if bidding "
                                                  "is over")
    product_img = fields.Binary(related="product_id.image_1920")
    product_description = fields.Text(related="product_id.description_sale",
                                      string="Auction Product Description")

    @api.onchange('template_id', 'product_id')
    def _onchange_template_id(self):
        """summary:
            function to add name automatically"""
        if self.product_id:
            self.name = f"Auction for {self.product_id.name}"

    @api.constrains('end_time', 'start_time')
    def _check_end_date(self):
        """
            Summary:
                start and end date validation function
        """
        for record in self:
            if record.end_time and record.start_time and record.end_time <= record.start_time:
                raise ValidationError(
                    record.env._('End time should be greater than start time'))

    @api.constrains('extend_time')
    def _check_extend_time(self):
        """Summary:
                function to validate extended time whether it is greater than
                end time."""
        for record in self:
            if record.extend_time:
                if record.end_time and record.extend_time <= record.end_time:
                    raise ValidationError(
                        record.env._('This time is not greater than the old time (%s)', record.end_time))

    def _send_extend_notification(self):
        """Send notification to subscribers when extended time is updated."""
        template_id = self.env.ref(
            'website_bargain.email_template_auction_extended', raise_if_not_found=False)
        for record in self:
            if record.is_extend_auction_notification and template_id and record.bargain_subscribers_ids:
                emails = [s.email for s in record.bargain_subscribers_ids if s.email]
                if emails:
                    template_id.send_mail(
                        record.id,
                        email_values={'email_to': ','.join(emails)},
                        force_send=True,
                    )

    def write(self, vals):
        res = super().write(vals)
        if 'extend_time' in vals:
            self._send_extend_notification()
        return res

    def action_confirm(self):
        """
            Summary:
                   button function to confirm auction and will
                   make product as published
        """
        for auction in self:
            if self.search([('product_id', '=', auction.product_id.id),
                            ('state', '=', 'running')]):
                raise ValidationError(
                    auction.env._('Already an auction is running for this product please'
                                  ' close it to continue'))
            if auction.end_time <= fields.Datetime.now():
                raise ValidationError(auction.env._('End time is already over'))
            auction.product_id.is_published = True
            auction.product_id.website_id = auction.website_id
            auction.write({'state': 'confirmed'})

    def action_reset_to_draft(self):
        """
            Summary:
                button function to reset the auction to draft
        """
        for auction in self:
            auction.product_id.is_auction = False
            auction.write({'state': 'draft'})

    def action_run_auction(self):
        """
            Summary:
                button function to start auction manually
        """
        for auction in self:
            if self.search([('product_id', '=', auction.product_id.id),
                            ('state', '=', 'running')]):
                raise ValidationError(
                    auction.env._('Already an auction is running for this product '
                                  'please close it to continue'))
            auction.product_id.is_auction = True
            auction.write({'state': 'running'})

    def action_complete(self):
        """
            Summary:
                button function to end auction manually and process winner
        """
        for auction in self:
            auction._process_auction_end()

    def action_close(self):
        """
            Summary:
                button function to close auction
        """
        for auction in self:
            auction.product_id.is_auction = False
            auction.product_id.is_published = False
            auction.write({'state': 'closed'})

    def send_email_notification(self):
        """
        Summary:
            Function for sending auction notification for admin e ending if
            enabled
        """
        # Get the email template for the admin notification
        template_id = self.env.ref(
            'website_bargain.admin_email_template')
        # Find all running auctions that have notification enabled and have
        # not been sent yet
        auctions = self.search([('state', '=', 'running'),
                                ('is_activate', '=', True),
                                ('notify_on', '>', 0),
                                ('is_notification_send', '=', False)])
        # Loop through the auctions that need to be notified
        for auction in auctions:
            time_unit = auction.notify_selection if auction.notify_selection in ('days', 'hours', 'minutes', 'seconds') else None
            # Check if it's time to send the notification
            if time_unit:
                next_notification = auction.end_time - timedelta(
                    **{time_unit: auction.notify_on})
                if next_notification <= fields.Datetime.now():
                    # Send the notification email and set the flag to True
                    if template_id:
                        template_id.send_mail(auction.id, force_send=True)
                    auction.is_notification_send = True

    def auction_auto_start(self):
        """
            Summary:
                Cron function for auction auto start when its start
                time and also will send notification to customers about auction
        """
        # Get all confirmed auctions
        auctions = self.search([('state', '=', 'confirmed')])
        # Get the email template for auction start notification
        template_id = self.env.ref(
            'website_bargain.email_template_auction_start')
        # Get the emails of all the bidders and sale order partners
        bidders = self.env['bargain.information'].search(
            [('bidder_id', '!=', False)]
        ).mapped('bidder_id.email')
        sale_orders_partner = self.env['sale.order'].search(
            [('state', '=', 'sale')]).mapped('partner_id.email')
        # Loop through the auctions and check if any auction's start time has arrived
        for auction in auctions:
            if auction.start_time <= fields.Datetime.now():
                # Set the product as an auction and update the website
                auction.product_id.is_auction = True
                auction.product_id.website_id = auction.website_id
                auction.write({'state': 'running'})
                # Send email notifications to all the bidders and sale order partners
                emails = [email for email in set(sale_orders_partner + bidders) if email]
                if template_id and emails:
                    template_id.send_mail(
                        auction.id,
                        email_values={'email_to': ','.join(emails)},
                        force_send=True,
                    )

    def _process_auction_end(self):
        """Process auction end: determine winner, create draft quotation, and send notifications."""
        for auction in self:
            if auction.state in ('finished', 'closed'):
                continue

            placed_bids = auction.bargain_information_ids.filtered(
                lambda r: r.status == 'Bid Placed'
            ).sorted(key=lambda r: r.bid_offer)

            auction.write({'state': 'finished'})
            auction.product_id.is_auction = False
            auction.product_id.is_published = False

            sender_email = auction.auction_manager_id.email or auction.env.company.email

            # Subscriber bidding ended notification
            if auction.is_bid_end_notification and sender_email:
                subscribers = ','.join(
                    s.subscriber_id.email for s in auction.bargain_subscribers_ids if s.subscriber_id.email
                )
                if subscribers:
                    email_values = {
                        'email_from': sender_email,
                        'subject': f"Bidding Ended for {auction.name or ''}",
                        'email_to': subscribers,
                        'body_html': f"Bidding has ended for {auction.name or ''}. Thank you for participating."
                    }
                    self.env['mail.mail'].sudo().create(email_values).send()

            if not placed_bids:
                continue

            bid_record = placed_bids[-1]
            product = auction.product_id.product_variant_id or self.env['product.product'].search(
                [('product_tmpl_id', '=', auction.product_id.id)], limit=1
            )
            if not product:
                continue

            # Create draft sale order for the winner
            sale_order = self.env['sale.order'].sudo().create({
                'partner_id': bid_record.bidder_id.id,
                'state': 'draft',
            })
            sale_order.sudo().write({
                'order_line': [(0, 0, {
                    'product_id': product.id,
                    'product_uom_qty': 1,
                    'price_unit': bid_record.bid_offer,
                    'name': '(auction won) ' + (auction.name or ''),
                })]
            })
            # Send quotation email to winner
            template = (
                sale_order._find_mail_template()
                or self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
            )
            if template:
                try:
                    sale_order.sudo()._portal_ensure_token()
                except Exception as e:
                    _logger.warning("Failed to ensure portal token for sale order %s: %s", sale_order.id, e)
                email_values = {}
                if bid_record.bidder_id.email:
                    email_values['email_to'] = bid_record.bidder_id.email
                if bid_record.bidder_id:
                    email_values['recipient_ids'] = [(4, bid_record.bidder_id.id)]
                if sender_email:
                    email_values['email_from'] = sender_email
                try:
                    template.sudo().send_mail(
                        sale_order.id,
                        force_send=True,
                        email_values=email_values,
                    )
                    sale_order.sudo().write({'state': 'sent'})
                except Exception as e:
                    _logger.warning("Failed to send quotation email for sale order %s: %s", sale_order.id, e)

            # Send winner notification
            if auction.is_winner_notification and bid_record.bidder_id.email and sender_email:
                data = f"You have won in {auction.name or ''}. Kindly pay now and collect the product from our website."
                email_values = {
                    'email_from': sender_email,
                    'subject': 'Won ' + (auction.name or ''),
                    'email_to': bid_record.bidder_id.email,
                    'body_html': data
                }
                self.env['mail.mail'].sudo().create(email_values).send()

            # Send loser notification
            if auction.is_loser_notification and sender_email:
                loser_emails = [
                    record.bidder_id.email for record in auction.bargain_information_ids
                    if record.bidder_id.id != bid_record.bidder_id.id and record.bidder_id.email
                ]
                if loser_emails:
                    data = f"You have lost in {auction.name or ''}. Better luck next time, thank you for your effort and time."
                    email_values = {
                        'email_from': sender_email,
                        'subject': 'Lost ' + (auction.name or ''),
                        'email_to': ','.join(set(loser_emails)),
                        'body_html': data
                    }
                    self.env['mail.mail'].sudo().create(email_values).send()

    def auction_auto_end(self):
        """Cron function to auto-finish expired running auctions and notify winners/losers"""
        now = fields.Datetime.now()
        auctions = self.search([('state', '=', 'running')])
        for auction in auctions:
            effective_end = auction.extend_time or auction.end_time
            if effective_end and effective_end <= now:
                auction._process_auction_end()
