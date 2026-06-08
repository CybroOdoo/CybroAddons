/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { WebsiteSale } from "@website_sale/interactions/website_sale";

patch(WebsiteSale.prototype, {
    setup() {
        super.setup();

        /** function to add timer and check the time **/
//        const modal_title = document.querySelector('#modal_title');
//        const modal_message = document.querySelector('#modal_message');
        const product_name = this.el.querySelector('input[name="auction_product_id"]')?.value;
        const auction_id_status = this.el.querySelector('input[name="auction_id"]')?.value;
        const bellIcon = this.el.querySelector('#subscribe_bid');

        // Maintain Subscribe status
        if (auction_id_status !== undefined) {
            rpc('/subscribe/status', { auction_id: auction_id_status }).then((data) => {
                if (data) {
                    bellIcon.style.color = 'red';
                    bellIcon.classList.remove('fa-bell-o');
                    bellIcon.classList.add('fa-bell');
                    bellIcon.innerHTML = 'Unsubscribe';
                } else {
                    bellIcon.style.color = '#007bff';
                    bellIcon.classList.remove('fa-bell');
                    bellIcon.classList.add('fa-bell-o');
                    bellIcon.innerHTML = 'Subscribe';
                }
            });
        }

        // Hide "Add to Cart" button if AUCTION ON
        const auctionText = this.el.querySelector('#modal_message');
        if (auctionText) {
            document.querySelectorAll('.o_wsale_product_btn').forEach((values) => {
                if (values.nextElementSibling?.innerHTML === 'AUCTION ON') {
                    values.style.display = "none";
                }
            });
        }

        // Auction Timer Logic
        const product_id = this.el.querySelector('input[name="auction_product_id"]')?.value;
        const auction_id = this.el.querySelector('input[name="auction_id"]')?.value;
        let timerId;

        if (product_id) {
            const product_product_id = this.el.querySelector('input[name="product_product_id"]')?.value;
            rpc('/auction/timer', {
                product_id,
                auction_id
            }).then((data) => {
                if (new Date() > new Date(data['end_time'])) {
                    if (data['extend_time']) {
                        if (new Date() > new Date(data['extend_time'])) {
                            rpc('/auction/close', { product_id, auction_id }).then(() => {
                                rpc('/shop/sale/order', {
                                    product_product_id,
                                    product_id,
                                    auction_id
                                });
                            });
                            window.location.href = '/shop';
                        }
                    } else {
                        rpc('/auction/close', { product_id, auction_id }).then(() => {
                            rpc('/shop/sale/order', {
                                product_product_id,
                                product_id,
                                auction_id
                            });
                        });
                        window.location.href = '/shop';
                    }
                } else {
                    const self = this;
                    timerId = setInterval(function () {
                        const time_key = data['extend_time'] ? 'extend_time' : 'end_time';
                        const time_remaining = new Date(data[time_key]) - new Date();
                        const days = Math.floor(time_remaining / (1000 * 60 * 60 * 24));
                        const hours = Math.floor((time_remaining / (1000 * 60 * 60)) % 24);
                        const minutes = Math.floor((time_remaining / (1000 * 60)) % 60);
                        const seconds = Math.floor((time_remaining / 1000) % 60);
                        if (self.el.querySelector('#timer')) {
                            self.el.querySelector('#timer').innerHTML =
                                `${days}d. ${hours}h. ${minutes}m. ${seconds}s.`;
                        }
                        if (time_remaining <= 0) {
                            clearInterval(timerId);
                        }
                    }, 1000);
                    const time_key = data['extend_time'] ? 'extend_time' : 'end_time';
                    const time_remaining = new Date(data[time_key]) - new Date();
                    if (time_remaining <= 0) {
                        window.location.href = '/shop';
                    }
                }
            });
        }

        /** Event Listeners **/
        this.el.querySelector('#subscribe_bid')?.addEventListener('click', this._clickSubscribe.bind(this));
        this.el.querySelector('#place_bid_button')?.addEventListener('click', this._placeBid.bind(this));
        this.el.querySelector('#hide_modal')?.addEventListener('click', this._hideModal.bind(this));
        this.el.querySelector('.js_add_cart')?.addEventListener('click', this._buyNow.bind(this));
    },

    /** Function to hide auction messages after 5 seconds **/
    timeout() {
        const msg = this.el.querySelector('#auction_messages');
        if (msg) {
            setTimeout(() => {
                msg.style.display = "none";
            }, 5000);
        }
    },

    /** Function to handle subscription to auction updates **/
    _clickSubscribe() {
        const product_id = this.el.querySelector('input[name="auction_product_id"]')?.value;
        const auction_id = this.el.querySelector('input[name="auction_id"]')?.value;
        const bellIcon = this.el.querySelector('#subscribe_bid');
        const messages = this.el.querySelector('#auction_messages');

        if (!bellIcon || !messages) return;

        if (bellIcon.innerHTML === 'Subscribe') {
            bellIcon.style.color = 'red';
            bellIcon.classList.remove('fa-bell-o');
            bellIcon.classList.add('fa-bell');
            bellIcon.innerHTML = 'Unsubscribe';
            rpc('/subscribe/bid', {
                text: 'subscribe',
                product_id,
                auction_id
            }).then((data) => {
                messages.innerHTML = data;
                messages.classList.remove('alert-warning');
                messages.classList.add('alert-success');
                messages.style.display = "block";
                this.timeout();
            });
        } else {
            bellIcon.style.color = '#007bff';
            bellIcon.classList.remove('fa-bell');
            bellIcon.classList.add('fa-bell-o');
            bellIcon.innerHTML = 'Subscribe';
            rpc('/subscribe/bid', {
                text: 'unsubscribe',
                auction_id
            }).then((data) => {
                messages.classList.add('alert-warning');
                messages.innerHTML = data;
                messages.style.display = "block";
                this.timeout();
            });
        }
    },

    /** Function to handle adding products to cart **/
    async _onClickAdd(ev) {
        ev.preventDefault();
        const def = () => {
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
    _submitForm() {
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

    /** Function to place a bid **/
    _placeBid() {
        const bid_amount_input = this.el.querySelector('input[id="bid_amount"]');
        const bid_amount = parseFloat(this.el.querySelector('input[id="bid_amount"]')?.value);
        const min_amount = parseFloat(this.el.querySelector('#min_amount')?.innerHTML);
        const product_id = this.el.querySelector('input[name="auction_product_id"]')?.value;
        const auction_id = this.el.querySelector('input[name="auction_id"]')?.value;
        const messages = this.el.querySelector('#auction_messages');
        const modal_title = document.querySelector('#modal_title');
        const modal_message = document.querySelector('#modal_message');

        if (!bid_amount_input.value || isNaN(bid_amount) || bid_amount <= 0) {
            modal_title.innerHTML = "Invalid Bid!";
            modal_message.innerHTML = "Please enter a valid bid amount before placing a bid.";
            $('#modal_product_warning').appendTo('body').modal('show');
            return;
        }

        if (min_amount >= bid_amount) {
            modal_title.innerHTML = "Warning!";
            modal_message.innerHTML = "Please check the minimum bid amount";
            $('#modal_product_warning').appendTo('body').modal('show');

        } else {
            rpc('/place_bid', {
                bid_amount,
                product_id,
                auction_id
            }).then((data) => {
                if (data) {
                    messages.innerHTML = data['bid_placed'];
                    messages.style.display = "block";
                    this.timeout();
                    window.location.reload();
                } else {
                    modal_title.innerHTML = "Same amount placed";
                    modal_message.innerHTML =
                        "You have already placed this amount. Please reconsider your bid amount";
                    $('#modal_product_warning').appendTo('body').modal('show');
                }
            });
        }
    },

    /** Hide modal **/
    _hideModal() {
        $('#modal_product_warning').modal('hide');
    },

    /** Buy now button **/
    _buyNow() {
        const product_id = this.el.querySelector('input[name="auction_product_id"]')?.value;
        const product_template_id = this.el.querySelector('input[name="product_product_id"]')?.value;
        const auction_id = this.el.querySelector('input[name="auction_id"]')?.value;
        const modal_title = this.el.querySelector('#modal_title');
        const modal_message = this.el.querySelector('#modal_message');

        rpc('/buy/now', {
            product_id: parseInt(product_template_id),
            auction_id: auction_id,
            auction_product_id: product_id,
            add_qty: 1
        }).then(() => {});
        rpc('/auction/close', {
            product_id: product_id,
            auction_id: auction_id
        });
        modal_title.innerHTML = "Success";
        modal_message.innerHTML =
            "You will get an email, please confirm and pay now. You will be redirected to the home page.";
        $('#modal_product_warning').modal('show');
        setTimeout(() => {
            window.location.href = '/shop';
        }, 5000);
    },
});
