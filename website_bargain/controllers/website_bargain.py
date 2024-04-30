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
from odoo import fields, http
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class WebsiteAuction(WebsiteSale):
    """This class enables is used to view the timer and related functions
        of bidding,buy now and other routes
        _prepare_product_values(self, product, category, search, **kwargs):
                This function is inbuilt function in website sale and its
                supered here and pass auction values in this function
        auction_timer(self, auction_id):
                This function gets the auction id and pass auction timing
                details to website
        buy_now(self, auction_id, product_id):
                Its the function for button in buy now,in this function a new
                sale order is created and send to the customer through email
        def auction_close(self, auction_id):
                Function gets the auction id and move the auction stage to
                finished and make the product unavailable from website
        winner_sale_order(self, auction_id, **post):
                Makes a sale order to the winner and id notifications are
                enabled it will send a email to the winners or losers
        subscribe(self, auction_id, **post):
                Used to add subscribers from website to database
        place_bid(self, auction_id, **post):
                When place bid button is triggered it will call this function
                 and the bidders details will be added to database and
                  if enabled it will send notification to subscribers
        bidders(self, product_id):
                Route to pass bidders details to website
        bid_cancel(self, bidders):
                Function to cancel the bid"""

    def _prepare_product_values(self, product, category, search, **kwargs):
        """Summary:
                Function is used to pass auction details by supering
                this function because its already defined it websitesale
            Args:
                product:pass the object product
                category:pass the category if enabled
                kwargs:used to pass variable to function
            Return:
                Values is updated with auction and current website and
                 passed to website sale"""
        values = super()._prepare_product_values(product, category, search,
                                                 **kwargs)
        current_website = request.website
        auction = request.env['website.bargain'].sudo().search_read([])
        values.update({
            'auction': auction,
            'website': current_website
        })
        return values

    @http.route('/auction/timer', type='json', auth='user', csrf=False)
    def auction_timer(self, auction_id):
        """Summary:
                Function to pass timer details from auction like start
                 time,end time,extended time
            Args:
                auction_id:used to get auction id from website
            Return:
                Values which include start_time,end time,extended
                 time and state id"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        values = {
            'start_time': auction.start_time,
            'end_time': fields.Datetime.context_timestamp(auction,
                                                          auction.end_time),
            'state': auction.state,
        }
        if auction.extend_time:
            values['extend_time'] = fields.Datetime.context_timestamp(auction,
                                                                      auction.extend_time)
        return values

    @http.route('/auction/close', type='json', auth='user', csrf=False)
    def auction_close(self, auction_id):
        """Summary:
            Function to close auction when a customer buys
            a product instantly or the auction is ended
        Args:
            auction_id: used to get auction id from website
        Return:
            a string auction ended to website"""
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        auction.product_id.is_auction = False
        auction.product_id.is_published = False
        auction.write({'state': 'finished'})
        return "auction ended"

    @http.route('/place_bid', type='json', auth='user', csrf=False)
    def place_bid(self, auction_id, **post):
        """Summary:
                When place bid button is clicked it will trigger this function
                 and will add bidders details to backend and will send
                 notification to the subscribers if its enabled
            Args:
                auction_id:used to get auction id from website
                post:used to get bid amount from frontend
            Return:
                A message bid placed and suction details"""
        bid_amount = post.get('bid_amount')
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        bidder_total = auction.bargain_information_ids.search_count(
            [('bidder_id', '=', request.env.user.partner_id.id),
             ('bid_offer', '=', bid_amount)])
        if bidder_total >= 1:
            return False
        else:
            auction.bargain_information_ids.sudo().create({
                'bidder_id': request.env.user.partner_id.id,
                'auction_id': auction.id,
                'bid_offer': bid_amount,
                'status': 'Bid Placed'
            })
            if auction.is_subscriber_start_notification and not auction.is_send_mail:
                data = 'Bidding has started for ' + auction.name + '. Please check our website for more details.'
                subscribers = ""
                for record in auction.bargain_subscribers_ids:
                    subscribers += record.subscriber_id.email + ','
                email_values = {'email_from': auction.auction_manager_id.email,
                                'subject': 'Bidding Started for ' + auction.name,
                                'email_to': subscribers, 'body_html': data}
                request.env['mail.mail'].sudo().create(email_values).send()
                auction.is_send_mail = True
                auction.write({'is_send_mail': True})

            if auction.is_new_bid_notification:
                data = 'A new bid has been placed with amount ' + str(
                    bid_amount) + ',on ' \
                       + auction.name + ',by ' + request.env.user.partner_id.name \
                       + 'please check into ' \
                         'our website'
                subscribers = " "
                for record in auction.bargain_subscribers_ids:
                    subscribers += record.subscriber_id.email + ','
                email_values = {'email_from': auction.auction_manager_id.email,
                                'subject': 'New Bid Placed on ' + auction.name,
                                'email_to': subscribers, 'body_html': data}
                request.env['mail.mail'].sudo().create(email_values).send()
            values = ({
                'bid_placed': 'Bid Placed',
                'auction': auction
            })

            return values

    @http.route('/bidders/<model("product.template"):product_id>', type='http',
                auth='user', csrf=False, website=True)
    def bidders(self, product_id):
        """
        This method is used to fetch the details of the bidders participating in
         an auction and render them on the website.
        Args:
            product_id: A product template model object.
        Returns:
            A rendered HTML template with information about the bidders in the
            auction."""
        auction = request.env['website.bargain'].sudo().search(
            [('product_id', '=', product_id.id), ('state', '=', 'running')])
        bidders_information = request.env['bargain.information'].sudo().search(
            [('auction_id', '=', auction.id)],
            order='bid_offer desc')
        values = ({
            'bidders_information': bidders_information,
            'product_id': product_id,
        })
        return request.render('website_bargain.bidders_information', values)

    @http.route('/bid/cancel/<model("bargain.information"):bidders>',
                type='http', auth='user', csrf='false')
    def bid_cancel(self, bidders):
        """This function is for cancel the bid
            Args:
                bidders:Bidders name will be getting here
            Returns:It returns previous page"""
        bidders.status = 'cancelled'
        previous_web_url = request.httprequest.headers.get('referer')
        return request.redirect(previous_web_url)

    @http.route('/shop/sale/order', type='json', auth='public', website=True,
                csrf=False)
    def winner_sale_order(self, auction_id, **post):
        """
            This route creates a draft sale order for the winner of an auction
            and sends notifications for winning and losing.
        Args:
            auction_id: the ID of the auction obtained from the frontend
            post: used to get data of product from frontend
        Returns:
            True"""
        # Get the ID of the product from the post data
        product_product_id = post.get('product_product_id')
        # Find the auction with the given ID
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        auction.write({'state': 'finished'})
        if auction.is_bid_end_notification:
            data = 'Bidding has ended for ' + auction.name + '. Thank you for participating.'
            subscribers = ""
            for record in auction.bargain_subscribers_ids:
                subscribers += record.subscriber_id.email + ','
            email_values = {'email_from': auction.auction_manager_id.email,
                            'subject': 'Bidding Ended for ' + auction.name,
                            'email_to': subscribers, 'body_html': data}
            request.env['mail.mail'].sudo().create(email_values).send()
        # Find the highest bidder for the auction
        bid_record = auction.bargain_information_ids.filtered(
            lambda r: r.status == 'Bid Placed').sorted(
            key=lambda r: r.bid_offer)[-1]
        # Create a draft sale order for the winner
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': bid_record.bidder_id.id,
            'state': 'draft',
        })
        # Add the product to the sale order and set the price to the bid offer
        sale_order.sudo().write({
            'order_line': [(0, 0, {
                'product_id': int(product_product_id),
                'product_uom_qty': 1,
                'price_unit': bid_record.bid_offer,
                'name': 'auction won',
            })]
        })
        mail_compose_message = request.env['mail.compose.message']
        so_mcm_vals = sale_order.sudo().action_quotation_send().get('context',
                                                                    {})
        compose_msg = mail_compose_message.sudo().with_context(
            so_mcm_vals).create({})
        compose_msg.sudo().action_send_mail()
        # Send a notification email to the winner and/or losers, if enabled
        if auction.is_winner_notification:
            data = "You have won in " + auction.name + " Kindly pay now and" \
                                                       " collect the product " \
                                                       "from our website"
            email_values = {
                'email_from': auction.auction_manager_id.email,
                'subject': 'Won ' + auction.name,
                'email_to': bid_record.bidder_id.email,
                'body_html': data
            }
            request.env['mail.mail'].sudo().create(email_values).send()
        if auction.is_loser_notification:
            data = "You have lost in " + auction.name + "Better luck next time"\
                                                        " thank you for your " \
                                                        "effort and time"
            email_to = ''
            for record in auction.bargain_information_ids:
                if record.bidder_id.id != bid_record.bidder_id.id:
                    email_to += record.bidder_id.email + ','
            email_values = {
                'email_from': auction.auction_manager_id.email,
                'subject': 'Lost ' + auction.name,
                'email_to': email_to,
                'body_html': data
            }
            request.env['mail.mail'].sudo().create(email_values).send()
        return True

    @http.route('/subscribe/bid', type='json', auth='user', csrf=False)
    def subscribe(self, auction_id, **post):
        """
        Endpoint to manage subscription to an auction
         auction_id: integer ID of the auction being subscribed to/unsubscribed
         text: string indicating whether the user is subscribing or
         unsubscribing ('subscribe' or 'unsubscribe')
        return: string message indicating success or failure of
        subscription/unsubscription action
        """
        text = post.get('text')
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        if text == 'subscribe':
            if request.env.user.partner_id in \
                    auction.bargain_subscribers_ids.subscriber_id:
                return 'You have already subscribed'
            auction.bargain_subscribers_ids.sudo().create({
                'subscriber_id': request.env.user.partner_id.id,
                'auction_id': auction.id,
                'is_subscribed': True
            })
            return 'You have been successfully subscribed to this auction'
        elif text == 'unsubscribe':
            auction.bargain_subscribers_ids.sudo().search(
                [('subscriber_id', '=', request.env.user.partner_id.id),
                 ('auction_id', '=', auction.id)]).unlink()
            return 'Unsubscribed successfully'

    @http.route('/subscribe/status', type='json', auth='user', csrf=False)
    def subscribe_status(self, auction_id,  **post):
        """
        Controller method to handle subscription to an auction.
        """
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        is_subscribed = False
        for subscriber in auction.bargain_subscribers_ids:
            if subscriber.subscriber_id == request.env.user.partner_id:
                is_subscribed = subscriber.is_subscribed
                break

        return is_subscribed

    @http.route('/buy/now', type='json', auth='public', website=True,
                csrf=False)
    def buy_now(self, auction_id, product_id):
        """
        Args:
            auction_id: the ID of the auction obtained from the frontend
            product_id: the ID of the product used to get data from the frontend
        """
        # Find the auction with the given ID
        auction = request.env['website.bargain'].sudo().browse(int(auction_id))
        # Create a draft sale order for the winner
        sale_order = request.env['sale.order'].sudo().create({
            'partner_id': request.env.user.partner_id.id,
            'state': 'draft',
        })
        sale_order.sudo().write({
            'order_line': [(0, 0, {
                'product_id': int(product_id),
                'product_uom_qty': 1,
                'name': '(auction won)' + auction.name,
                'price_unit': auction.price_buy_now,
            })]
        })
        # Send a notification email to the winner
        mail_compose_message = request.env['mail.compose.message']
        so_mcm_vals = sale_order.sudo().action_quotation_send().get('context',
                                                                    {})
        compose_msg = mail_compose_message.sudo().with_context(
            so_mcm_vals).create({})
        compose_msg.sudo().action_send_mail()
