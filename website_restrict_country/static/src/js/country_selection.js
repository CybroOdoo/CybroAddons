odoo.define('website_restrict_company.countries', function(require) {
"use strict";
const ajax = require('web.ajax');
var publicWidget = require('web.public.widget');
  // Extended PublicWidget
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
            ajax.jsonRpc('/website/countries', 'call', { 'country_id': country_id})
            .then(result => {
               $(e.currentTarget).parent().parent().html(result)
            });
        },
    });
});
