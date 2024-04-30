# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anfas Faisal K (odoo@cybrosys.com)
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
###############################################################################
from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class WebsiteBargain(models.Model):
    """This is the main class of website bargain where all the details are
        stored in this model
        _onchange_template_id:
            function for automatically add the auction name
        _check_end_date:
            function to validate the end date if it is higher than the start
            date
        _check_extend_time:
            function to validate extended time weather it is greater than end
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
                                         help="Set suction manager here",
                                         required=True)
    product_id = fields.Many2one(related='template_id.product_id', store=True,
                                 string='Product', readonly=False,
                                 help="Select the product", required=True)
    name = fields.Char(string='Auction Name', help="Auctions name")
    currency_id = fields.Many2one('res.currency', 'Currency',
                                  default=lambda
                                      self: self.env.user.company_id.currency_id.id,
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
                                    help="Price of the product if its"
                                         " immediately buying")
    start_time = fields.Datetime(string='Start Date Time', required=True,
                                 default=fields.Datetime.today(),
                                 help="Auction start time")
    end_time = fields.Datetime(string='End Date Time', required=True,
                               help="Auction start time")
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
    notify_on = fields.Integer(string='Notify before', default='5',
                               help="Set notification time here")
    notify_selection = fields.Selection(
        [('days', "Days"), ('hours', "Hours"), ('minutes', "Minutes"),
         ('seconds', "Seconds")], default='minutes')
    is_notification_send = fields.Boolean(string='Notification Send',
                                          help='If notification send manually '
                                               'you can enable this field '
                                               'to restrict '
                                               'sending notification before '
                                               'the time added')
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
                                                    help="Send subscribers the"
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
        if self.end_time <= self.start_time:
            raise ValidationError(
                _('End time should be greater than start time'))

    @api.constrains('extend_time')
    def _check_extend_time(self):
        """Summary:
                function to validate extended time weather it is greater than
                end time and after saving will send notification to subscribers
                 if enabled"""
        if self.extend_time:
            if self.extend_time <= self.end_time:
                raise ValidationError(
                    _('This time is not greater than the old time(' + str(
                        self.end_time) + ')'))
            if self.is_extend_auction_notification:
                template_id = self.env.ref(
                    'website_bargain.email_template_auction_extended')
                email_to = ''
                for subscriber in self.bargain_subscribers_ids:
                    email_to += subscriber.email + ','
                template_id.email_to = email_to
                template_id.send_mail(self.id, force_send=True)

    def action_confirm(self):
        """
            Summary:
                   button function to confirm auction and will
                   make product as published
        """
        if self.search([('product_id', '=', self.product_id.id),
                        ('state', '=', 'running')]):
            raise ValidationError(
                _('Already an auction is running for this product please'
                  ' close it to continue'))
        if self.end_time <= fields.Datetime.today():
            raise ValidationError(_('End time is already over'))
        self.product_id.is_published = True
        self.product_id.website_id = self.website_id
        self.write({'state': 'confirmed'})

    def action_reset_to_draft(self):
        """
            Summary:
                button function to reset the auction to draft
        """
        self.product_id.is_auction = False
        self.write({'state': 'draft'})

    def action_run_auction(self):
        """
            Summary:
                button function to start auction manually
        """
        if self.search([('product_id', '=', self.product_id.id),
                        ('state', '=', 'running')]):
            raise ValidationError(
                _('Already an auction is running for this product '
                  'please close it to continue'))
        self.product_id.is_auction = True
        self.write({'state': 'running'})

    def action_complete(self):
        """
            Summary:
                button function to end auction manually
        """
        self.product_id.is_auction = False
        self.product_id.is_published = False
        self.write({'state': 'finished'})

    def action_close(self):
        """
            Summary:
                button function to close auction
        """
        self.product_id.is_auction = False
        self.product_id.is_published = False
        self.write({'state': 'closed'})

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
            # Map the time unit to a string for timedelta
            time_unit_map = {'days': 'days', 'hours': 'hours',
                             'minutes': 'minutes', 'seconds': 'seconds'}
            time_unit = time_unit_map.get(auction.notify_selection)
            # Check if it's time to send the notification
            if time_unit:
                next_notification = auction.end_time - timedelta(
                    **{time_unit: auction.notify_on})
                if next_notification <= fields.Datetime.today():
                    # Send the notification email and set the flag to True
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
        bidders = self.env['bargain.information'].search([]).mapped(
            'bidder_id.email')
        sale_orders_partner = self.env['sale.order'].search(
            [('state', '=', 'sale')]).mapped('partner_id.email')
        # Loop through the auctions and check if any auction's start time has arrived
        for auction in auctions:
            if auction.start_time <= fields.Datetime.today():
                # Set the product as an auction and update the website
                auction.product_id.is_auction = True
                auction.product.website_id = auction.website_id
                auction.write({'state': 'running'})
                # Send email notifications to all the bidders and sale order partners
                email_to = ""
                for partner in sale_orders_partner:
                    email_to += partner + ','
                for bidder in bidders:
                    email_to += bidder + ','
                template_id.email_to = email_to
                template_id.send_mail(auction.id, force_send=True)
