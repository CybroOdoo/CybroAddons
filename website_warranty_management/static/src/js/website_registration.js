/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

// Disabling previous JS as we are using standard form submission and pre-prepared data in controller
publicWidget.registry.WarrantyClaim = publicWidget.Widget.extend({
    selector: '.warranty-claim-widget',
});

export default publicWidget.registry.WarrantyClaim;