/** @odoo-module **/
import { renderToElement } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";





publicWidget.registry.Reservation = publicWidget.Widget.extend({
    selector: '.reservation',
    start() {
        // Time Change Function
        const inputEle = document.getElementById('timeInput');
        if (inputEle) {
            inputEle.addEventListener('change', () => {
                const timeSplit = inputEle.value.split(':');
                let hours = parseInt(timeSplit[0], 10);
                const minutes = timeSplit[1];
                let meridian;

                if (hours > 12) {
                    meridian = 'PM';
                    hours -= 12;
                } else if (hours < 12) {
                    meridian = 'AM';
                    if (hours === 0) {
                        hours = 12;
                    }
                } else {
                    meridian = 'PM';
                }
                alert(`${hours}:${minutes} ${meridian}`);
            });
        }
    }
});

publicWidget.registry.WebsiteNewsletter = publicWidget.Widget.extend({
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
            let data = await rpc('/subscribe_newsletter', {
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
