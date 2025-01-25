/** @odoo-module */
import PublicWidget from "@web/legacy/js/public/public_widget"
import { _t } from "@web/core/l10n/translation";
import { rpc } from "@web/core/network/rpc";

PublicWidget.registry.customSplash = PublicWidget.Widget.extend({
    selector: "#wrapwrap",
    events: {
        'click .btn-sub': 'onClickSubscribe',
    },
    async onClickSubscribe(ev) {
        let $button = $(ev.currentTarget)
        let $input = $(ev.currentTarget.parentElement).find('input')
        let $warning = $(ev.currentTarget.parentElement).find('.warning')
        if (this.emailCheck($input.val())) {
            if ($button.text() === "Subscribe") {
                const data = await rpc('/subscribe_newsletter', {
                    email: $input.val()
                })
                if (data) {
                    $warning.hide()
                    $input.css('pointer-events', 'none')
                    $button.css('background-color', 'green')
                    $button.text("Thanks")
                } else {
                    $warning.text("Already subscribed to the newsletter.")
                    $warning.show()
                }
            }
        } else {
            $warning.text("Enter a valid email.")
            $warning.show()
        }
    },
    emailCheck(str) {
        const specialChars = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return specialChars.test(str)
    }
})