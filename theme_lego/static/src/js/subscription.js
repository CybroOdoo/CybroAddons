/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.WebsiteSaleCart = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click .subscribe-btn': 'onClickSubscribe',
    },

    async onClickSubscribe(ev) {
        // Function for subscribe newsletter.
        const $button = $(ev.currentTarget);
        const $input = $(ev.currentTarget.parentElement).find('input');
        this.$el.removeClass('o_has_error').find('.form-control').removeClass('is-invalid');
        if ($input.val().match(/.+@.+/)) {
            let data = await rpc('/newsletter_subscription', {
                email: $input.val()
            });
            if (data) {
                $(ev.currentTarget.parentElement.parentElement).find('.warning').hide();
                $input.css('pointer-events', 'none');
                $button.css('background-color', 'green !important');
                $button.text("THANKS");
            } else {
                $(ev.currentTarget.parentElement.parentElement).find('.warning').text("Already subscribed to the newsletter.");
                $(ev.currentTarget.parentElement.parentElement).find('.warning').show();
            }
        } else {
            this.$el.addClass('o_has_error').find('.form-control').addClass('is-invalid');
            $(ev.currentTarget.parentElement.parentElement).find('.warning').text("Enter a valid email.");
            $(ev.currentTarget.parentElement.parentElement).find('.warning').show();
        }
    },
})