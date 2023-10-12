/* @odoo-module */
import { session } from "@web/session";
var rpc = require('web.rpc');
    const publicWidget = require("web.public.widget");
    /**
 * Cookie Consent Manager widget.
 *
 * This widget manages the display of the cookie consent bar and handles user actions related to cookies.
 */
    publicWidget.registry.CookieConsentManager =
      publicWidget.Widget.extend({
        selector: "#website_cookies_bar",
        events: {
          "click #cookies-consent-all": "hideCookie",
          "click #cookies-close": "hideCookie",
          "click #cookies-consent-essential": "hideCookie",
        },
        start : function (){
        /**
         * Start function for the widget.
         * If the user is not logged in, the modal is hidden.
         */
            if ( ! session.user_id )
                this.$target.find('.modal').hide();
        },
        hideCookie: async function (ev) {
        /**
         * Hide the cookie consent modal and send a request to enable cookies for the user.
         *
         * @param {Event} ev - The click event.
         */
            this.$target.find('.modal').hide();
            await rpc.query({
                model:'cookie.information',
                method : 'cookie_enabled',
                args : [session.user_id]
            })
           }
        });
