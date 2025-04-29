/** @odoo-module **/
    import publicWidget from "@web/legacy/js/public/public_widget";
    import { jsonrpc } from "@web/core/network/rpc_service";
    publicWidget.registry.PropertyView = publicWidget.Widget.extend({
        selector: 'div[id="property_container"]',
        events: {
            'click .property_action_buttons': '_changeView',
            'click .o_property_item': 'fetchPropertyItem',
            'click #auction_submit': '_submitAuction',
        },
        /** Hide and show the properties according to the action_id **/
        _changeView: function (ev) {
            var action_id = this.$(ev.currentTarget).data('action')
            this.$('.property_action_buttons').removeClass('active')
            this.$('#property_item_view').hide()
            this.$('#property_sales_view').hide()
            this.$('#property_rental_view').hide()
            this.$('#property_auction_view').hide()
            if (action_id == "0") {
                this.$('#property_item_view').show()
                this.$(ev.currentTarget).addClass('active')
            } else if (action_id == "2") {
                this.$(ev.currentTarget).addClass('active')
                this.$('#property-item').hide()
                this.$('#property_sales_view').show()
            } else if (action_id == "3") {
                $(ev.currentTarget).addClass('active')
                this.$('#property-item').hide()
                this.$('#property_rental_view').show()
            } else if (action_id == "1") {
                this.$('#property_auction_view').show()
                this.$(ev.currentTarget).addClass('active')
                jsonrpc('/property/auction', {}).then(function (result) {
                    this.$('.auction_cards').html(result)
                }.bind(this))
            }
        },
        /** Fetch all the properties **/
        fetchPropertyItem: function (ev) {
            var record_id = $(ev.currentTarget).data('property_id')
            window.location = '/property/' + record_id;
        },
        /** Submits the auction for the property **/
        _submitAuction: function (ev) {
            var property_id = this.$(ev.currentTarget).data('id');
            var bid_amount = parseFloat(this.$(`#property-${property_id}`).val());
            var last_bid = parseFloat(this.$(`#last-bid-${property_id}`).text());
            var bid_start = parseFloat(this.$(`#bid-start-${property_id}`).text());
            var toast = this.$('.toast')
            if (last_bid == '0') {
                last_bid = 1
            }
            if (bid_amount && last_bid && bid_start) {
                if (bid_amount <= last_bid || bid_amount <= bid_start) {
                    toast.addClass('show');
                } else {
                    jsonrpc("/property/auction/" + property_id + "/bid", {
                    bid_amount: bid_amount
                    }).then(function (result) {
                        $('#auction_button').click()
                    })
                }
            } else {
                toast.addClass('show');
            }
        },
    });
