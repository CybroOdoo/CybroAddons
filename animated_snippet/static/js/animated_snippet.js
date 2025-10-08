odoo.define('animated_snippet.pricing_page', function (require) {
    var PublicWidget = require('web.public.widget');
    var rpc = require('web.rpc');
    var AppPricingPage = PublicWidget.Widget.extend({
        selector: '.pricing-tables',  // The selector for the elements to which this widget applies
        events: {
            'change input': '_onSwitchChange'  // Event listener for input changes
        },

        start: function() {
            this._super.apply(this, arguments);
        },

        _initializeSwitches: function() {
            var self = this;
            this.$('.custom-switch').each(function(i) {
                var $this = $(this);
                var classes = $(this).attr("class"),
                    id      = $(this).attr("id"),
                    name    = $(this).attr("name");
                $(this).wrap('<div class="custom-switch" id="' + name + '"></div>');
                $(this).after('<label for="custom-switch-' + i + '"></label>');
                $(this).attr("id", "custom-switch-" + i);
                $(this).attr("name", name);
            });
        },

        _onSwitchChange: function(event) {
            $(".pricing-tables").toggleClass("plans--annually");
        }
    });
    PublicWidget.registry.AppPricingPage = AppPricingPage;
    return AppPricingPage;
});