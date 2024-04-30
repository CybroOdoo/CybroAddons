/** @odoo-module **/
import { WebsiteSale } from '@website_sale/js/website_sale';
import { jsonrpc } from "@web/core/network/rpc_service";

/**This is a JavaScript code written for the Odoo e-commerce platform.
It extends the functionality of the WebsiteSale module by adding an auction
feature, allowing customers to bid on products, and setting up a timer to track
the duration of the auction.**/
WebsiteSale.include({
    /**The start function initializes the auction timer when the page is loaded.
     It first checks if there are any ongoing auctions and hides the
     "add to cart" button if the product is being auctioned. Then, it retrieves
     the product and auction IDs from the input fields, sends an AJAX request to
      the server to fetch the auction details, and calculates the time remaining
       until the auction ends. If the auction has ended, the function redirects
        the user to the shop page, and if not, it sets up an interval to update
        the timer every second.**/
    start: function() {
        /** function to add timer and check the time **/
        this._super(...arguments);
        var modal_title = this.$('#modal_title')[0]
        var modal_message = this.$('#modal_message')[0]
        var product_name = this.$('input[name="auction_product_id"]').val();
        var auction_id_status = this.$('input[name="auction_id"]').val()
        var bellIcon = this.el.querySelector('#subscribe_bid');
        if (auction_id_status != undefined){
        jsonrpc('/subscribe/status', {
                'auction_id': auction_id_status,
            }).then((data) => {
            if (data){
            bellIcon.style.color = 'red'
            bellIcon.classList.remove('fa-bell-o')
            bellIcon.classList.add('fa-bell')
            bellIcon.innerHTML = 'Unsubscribe'
            }
            else {
            bellIcon.style.color = '#007bff'
            bellIcon.classList.remove('fa-bell')
            bellIcon.classList.add('fa-bell-o')
            bellIcon.innerHTML = 'Subscribe'
            }
            })
        }
        let auctionText = this.$('#modal_message')[0]
        if (auctionText) {
            $.each($('.o_wsale_product_btn'), (key, values) => {
                if (values.nextElementSibling.innerHTML == 'AUCTION ON') {
                    values.style.display = "none"
                }
            })
        }
        let product_id = this.$('input[name="auction_product_id"]').val();
        let auction_id = this.$('input[name="auction_id"]').val();
        let timerId; // variable to hold the ID of the interval timer
        if (product_id) {
            let product_product_id = this.$('input[name="product_product_id"]').val()
            jsonrpc('/auction/timer', {
                'product_id': product_id,
                'auction_id': auction_id
            }).then((data) => {
                if (new Date() > new Date(data['end_time'])) {
                    if (data['extend_time']) {
                        if (new Date() > new Date(data['extend_time'])) {
                            jsonrpc('/auction/close', {
                                'product_id': product_id,
                                'auction_id': auction_id
                            }).then(() => {
                                jsonrpc('/shop/sale/order', {
                                    'product_product_id': product_product_id,
                                    'product_id': product_id,
                                    'auction_id': auction_id
                                })
                            })
                            window.location.href = '/shop'
                        }
                    } else {
                        jsonrpc('/auction/close', {
                            'product_id': product_id,
                            'auction_id': auction_id
                        }).then(() => {
                            jsonrpc('/shop/sale/order', {
                                'product_product_id': product_product_id,
                                'product_id': product_id,
                                'auction_id': auction_id
                            })
                        })
                        window.location.href = '/shop'
                    }
                } else {
                    var self = this;
                    timerId = setInterval(function() {
                        var time_key = data['extend_time'] ? 'extend_time' : 'end_time'
                        var time_remaining = new Date(data[time_key]) - new Date()
                        var days = Math.floor(time_remaining / (1000 * 60 * 60 * 24));
                        var hours = Math.floor((time_remaining / (1000 * 60 * 60)) % 24);
                        var minutes = Math.floor((time_remaining / (1000 * 60)) % 60);
                        var seconds = Math.floor((time_remaining / 1000) % 60);
                        if (self.el.querySelector('#timer')) {
                            self.el.querySelector('#timer').innerHTML = days + "d." + " " + hours + "h." + " " + minutes + "m." + " " + seconds + "s."
                        }
                        if (time_remaining <= 0) {
                            clearInterval(timerId);
                        }
                    }, 1000);
                    var time_key = data['extend_time'] ? 'extend_time' : 'end_time'
                    var time_remaining = new Date(data[time_key]) - new Date()
                    if (time_remaining <= 0) {
                        window.location.href = '/shop';
                    }
                }
            })
        }
    },
    events: {
        /** Click event for subscribe button**/
        'click #subscribe_bid': '_clickSubscribe',

         /**Click event for add to cart and buy now buttons**/
        'click #add_to_cart, .o_we_buy_now, #products_grid .o_wsale_product_btn .a-submit': 'async _onClickAdd',

         /**Click event for place bid button**/
        'click #place_bid_button': '_placeBid',

         /**Click event for hide modal button**/
        'click #hide_modal': '_hideModal',

         /**Click event for buy now button**/
        'click .js_add_cart': '_buyNow'
    },
    /** Function to hide auction messages after 5 seconds **/
    timeout: function() {
        var self = this;
        setTimeout(function() {
            self.el.querySelector('#auction_messages').style.display = "none"
        }, 5000)
    },
    /** Function to handle subscription to auction updates **/
    _clickSubscribe: function() {
        // Get product and auction IDs
        let product_id = this.$('input[name="auction_product_id"]').val()
        let auction_id = this.$('input[name="auction_id"]').val();

        // Get subscribe button and auction messages elements
        var bellIcon = this.el.querySelector('#subscribe_bid');
        var messages = this.el.querySelector('#auction_messages')

        // If button says "Subscribe", subscribe user to auction updates
        if (bellIcon.innerHTML == 'Subscribe' ) {
            bellIcon.style.color = 'red'
            bellIcon.classList.remove('fa-bell-o')
            bellIcon.classList.add('fa-bell')
            bellIcon.innerHTML = 'Unsubscribe'
            jsonrpc('/subscribe/bid', {
                'text': 'subscribe',
                'product_id': product_id,
                'auction_id': auction_id
            }).then((data) => {
                messages.innerHTML = data
                messages.classList.remove('alert-warning')
                messages.classList.add('alert-success')
                messages.style.display = "block"
                this.timeout()
            })
        }
        /** Otherwise, unsubscribe user from auction updates **/
        else {
            bellIcon.style.color = '#007bff'
            bellIcon.classList.remove('fa-bell')
            bellIcon.classList.add('fa-bell-o')
            bellIcon.innerHTML = 'Subscribe'
            jsonrpc('/subscribe/bid', {
                'text': 'unsubscribe',
                'auction_id': auction_id
            }).then((data) => {
                messages.classList.add('alert-warning')
                messages.innerHTML = data
                messages.style.display = "block"
                this.timeout()
            })
        }
    },
    /** Function to handle adding products to cart **/
    _onClickAdd: function(ev) {
        ev.preventDefault();
        var def = () => {
            this.getCartHandlerOptions(ev);
            return this._handleAdd($(ev.currentTarget).closest('form'));
        };
        if ($('.js_add_cart_variants').children().length) {
            return this._getCombinationInfo(ev).then(() => {
                return !$(ev.target).closest('.js_product').hasClass("css_not_available") ? def() : Promise.resolve();
            });
        }
        return def();
    },
    /** Function to submit form when adding products to cart **/
    _submitForm: function() {
        const params = this.rootProduct;
        const $product = $('#product_detail');
        const productTrackingInfo = $product.data('product-tracking-info');
        if (productTrackingInfo) {
            productTrackingInfo.quantity = params.quantity;
            $product.trigger('add_to_cart_event', [productTrackingInfo]);
        }
        params.add_qty = params.quantity;
        params.product_custom_attribute_values = JSON.stringify(params.product_custom_attribute_values);
        params.no_variant_attribute_values = JSON.stringify(params.no_variant_attribute_values);
        delete params.quantity;
        return this.addToCart(params);
    },
    _placeBid: function() {
        /** Function to place a bid
         Get the bid amount and minimum amount from the page **/
        var bid_amount = parseFloat(this.$('input[id="bid_amount"]').val())
        var min_amount = parseFloat(this.$('#min_amount')[0].innerHTML)
        let product_id = this.$('input[name="auction_product_id"]').val()
        let auction_id = this.$('input[name="auction_id"]').val();
        var messages = this.$('#auction_messages')[0]
        if (min_amount >= bid_amount) {
            modal_title.innerHTML = "Warning!"
            modal_message.innerHTML = "Please check the minimum bid amount"
            this.$('#modal_product_warning').modal('show')
        } else {
            jsonrpc('/place_bid', {
                'bid_amount': bid_amount,
                'product_id': product_id,
                'auction_id': auction_id
            }).then((data) => {
                if (data){
                    messages.innerHTML = data['bid_placed']
                    messages.style.display = "block";
                    this.timeout()
                    window.location.reload()
                }
                else {
                    modal_title.innerHTML = "Same amount placed"
                    modal_message.innerHTML = "You have already placed this amount. Please reconsider your bid amount"
                    this.$('#modal_product_warning').modal('show')
                }
            })
        }
    },
    /**Click event for hide modal button**/
    _hideModal: function() {
        this.$('#modal_product_warning').modal('hide')
    },
    _buyNow: function() {
        /** function for buy now button **/
        let product_id = this.$('input[name="auction_product_id"]').val()
        let product_template_id = this.$('input[name="product_product_id"]').val()
        let auction_id = this.$('input[name="auction_id"]').val();
        jsonrpc('/buy/now', {
            product_id: parseInt(product_template_id),
            'product_id': product_template_id,
            'auction_id': auction_id,
            'auction_product_id': product_id,
            'add_qty': 1
        }).then(function(data) {})
        jsonrpc('/auction/close', {
            'product_id': product_id,
            'auction_id': auction_id,
        })
        modal_title.innerHTML = "Success"
        modal_message.innerHTML = "You will get a email please confirm and pay now you will be redirected to home page"
        $('#modal_product_warning').modal('show')
        setTimeout(function() {
        window.location.href = '/shop'
        }, 5000)
    },
})
