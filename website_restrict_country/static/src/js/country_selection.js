/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service";
import publicWidget from "@web/legacy/js/public/public_widget";

  publicWidget.registry.Country_detail = publicWidget.Widget.extend({
    selector: ".js_countrymenu",
    events: {
        'click .js_countries': 'OnClickChangeCountry',
    },
    // Added a Click function to select the country
    OnClickChangeCountry: function(e) {
        event.preventDefault(e);
            var country_id = e.currentTarget.dataset['country_id']
            var self = this;
            jsonrpc('/website/countries', { 'country_id': country_id})
            .then(result => {
               $(e.currentTarget).parent().parent().html(result)
               window.location.reload()
            });
        },
    })
