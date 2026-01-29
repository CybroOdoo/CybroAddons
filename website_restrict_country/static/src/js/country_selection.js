odoo.define('website_restrict_company.countries', function(require) {
    "use strict";
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    // Extended PublicWidget
    publicWidget.registry.Country_detail = publicWidget.Widget.extend({
        selector: ".js_countrymenu",
        events: {
            'click .js_countries': 'OnClickChangeCountry',
            'click .dropdown-toggle': 'OnToggleDropdown'
        },

        // Toggle the dropdown visibility
        OnToggleDropdown: function(e) {
            e.preventDefault();
            $(e.currentTarget).next('.dropdown-menu').toggleClass('show');
        },

        // Added a Click function to select the country
        OnClickChangeCountry: function(e) {
            e.preventDefault();
            var country_id = e.currentTarget.dataset['country_id'];
            var self = this;
            ajax.jsonRpc('/website/countries', 'call', { 'country_id': country_id })
            .then(function(result) {
                if (result) {
                    // Update the dropdown button to show the selected country
                    var country_image_url = result.country_image_url;
                    var country_name = result.country_name;
                    var dropdownButton = $(e.currentTarget).closest('.js_countrymenu').find('.dropdown-toggle');
                    dropdownButton.html('<img src="' + country_image_url + '" width="30" height="20"/> ' + country_name);

                    // Close the dropdown
                    $(e.currentTarget).closest('.dropdown-menu').removeClass('show');
                    window.location.reload();
                }
            });
        },
    });
});
