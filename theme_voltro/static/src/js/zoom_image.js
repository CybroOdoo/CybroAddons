/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";


publicWidget.registry.zoomImage = publicWidget.Widget.extend({
        selector: ".voltro_product_images",

    // Define the events to be handled by the widget
    start: function () {
        var self = this;
        // Get the preview images
        var $images = this.$('.preview_image');
        // Hide images if there are more than 4
        if ($images.length > 4) {
            $images.slice(4).hide();
        }
    },

});