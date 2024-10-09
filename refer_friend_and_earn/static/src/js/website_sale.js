/** @odoo-module **/
  /**
 * This file  used control the visibility of 'I have points'
 */
import publicWidget from "@web/legacy/js/public/public_widget";
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
