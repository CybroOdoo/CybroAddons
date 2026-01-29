odoo.define('refer_friend_and_earn.refer_and_earn', function(require) {
  "use strict";
  /**
 * This file  used control the visibility of 'I have points'
 */
var publicWidget = require('web.public.widget');
publicWidget.registry.ReferAndEarn = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click .show_points': '_onClickShowPoints',
    },
// While click on the 'I have points', hide the text and shows the input field
     _onClickShowPoints: function (ev) {
        this.$el.find(".show_points").hide();
        this.$el.find('.point_form').removeClass('d-none');
    },
});
return publicWidget.registry.ReferAndEarn;
});
