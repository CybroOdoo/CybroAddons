/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.MarketplaceRating = publicWidget.Widget.extend({
    selector: '.s_tabs_main',
    events: {
        'click .prod_redirect': '_onProdRedirectClick',
        'click #post': '_onPostClick',
        'click #post_yes': '_onPostYesClick',
        'click #post_no': '_onPostNoClick',
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onProdRedirectClick: function (ev) {
        const $link = $(ev.currentTarget);
        const url = $link.attr("href");
        if (url) {
            const newUrl = url.replaceAll(' ', '-');
            $link.attr("href", newUrl);
        }
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onPostClick: function (ev) {
        const seller_id = $("#seller").val();
        const customer_id = $("#customer").val();
        const message_id = this.$("#msg").val();
        if (!message_id) {
            swal({
                text: "Please Fill Your Comments!",
                button: "Close!",
            });
        } else {
            let rating = 0;
            for (let i = 11; i <= 15; i++) {
                if (this.$("#rating" + i).prop("checked")) {
                    rating = this.$("#rating" + i).val();
                    break;
                }
            }
            jsonrpc("/web/dataset/call_kw/seller.review/rate_review", {
                model: 'seller.review',
                method: 'rate_review',
                args: [{
                    'seller_id': seller_id,
                    'customer_id': customer_id,
                    'rating': rating,
                    'message': message_id
                }],
                kwargs: {},
            }).then(function (data) {
                swal({
                    title: "Rated!",
                    text: "Thank You For Your Rating!",
                    icon: "success",
                    button: "Close!"
                }).then(function () {
                    location.reload();
                });
            });
        }
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onPostYesClick: function (ev) {
        this._recommend('yes');
    },

    /**
     * @private
     * @param {Event} ev
     */
    _onPostNoClick: function (ev) {
        this._recommend('no');
    },

    /**
     * @private
     * @param {string} recommend
     */
    _recommend: function (recommend) {
        const seller_id = $("#seller").val();
        const customer_id = $("#customer").val();
        jsonrpc("/web/dataset/call_kw/seller.recommend/recommend_func", {
            model: 'seller.recommend',
            method: 'recommend_func',
            args: [{
                'seller_id': seller_id,
                'customer_id': customer_id,
                'recommend': recommend,
            }],
            kwargs: {},
        }).then(function (data) {
            swal({
                text: "Thank You!",
                button: "Close!",
            });
        });
    },
});
