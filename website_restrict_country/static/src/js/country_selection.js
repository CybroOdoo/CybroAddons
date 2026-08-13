/** @odoo-module **/
/**
 * Frontend widgets for the Website Restrict Country module.
 *
 * - countrySelection: lets a visitor pick a country from the header dropdown.
 *   The selected country is sent to the `/website/countries` controller, which
 *   stores it as the website's default country and returns the re-rendered
 *   selection menu.
 * - buyNowRestricted: handles the red "Buy now" button shown when a product is
 *   not available in the selected country, showing the restriction message as
 *   a warning notification instead of starting a purchase.
 */
import { rpc } from "@web/core/network/rpc";
import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.countrySelection = publicWidget.Widget.extend({
    selector: ".js_countrymenu",
    events: {
        "click .js_countries": "onClickChangeCountry",
    },
    // Send the selected country to the server and refresh the page.
    onClickChangeCountry: function (e) {
        e.preventDefault();
        const countryId = e.currentTarget.dataset["country_id"];
        rpc("/website/countries", { country_id: countryId }).then((result) => {
            e.currentTarget.closest(".js_countrymenu").innerHTML = result;
            window.location.reload();
        });
    },
});

publicWidget.registry.buyNowRestricted = publicWidget.Widget.extend({
    selector: ".js_buy_now_restricted",
    events: {
        click: "onClickRestricted",
    },
    init: function () {
        this._super(...arguments);
        this.notification = this.bindService("notification");
    },
    // Block the purchase and warn that the product is unavailable here.
    onClickRestricted: function (e) {
        e.preventDefault();
        this.notification.add(this.el.dataset.message, { type: "warning" });
    },
});
