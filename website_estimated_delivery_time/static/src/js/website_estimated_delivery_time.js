/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.search_pin_number = publicWidget.Widget.extend({
    selector: '#search_website_pin_number',

    events: {
        'click #search_button': '_onClickSearchButton',
    },

    _showModal: function (modalId) {
        const modalEl = document.getElementById(modalId);
        if (!modalEl || !window.Modal) {
            return;
        }
        window.Modal.getOrCreateInstance(modalEl).show();
    },

    _onClickSearchButton: function () {
        const search_value = (this.$('#pin_number').val() || '').trim();
        const product_template_id = this.$('input[name="product_template_id"]').val()
            || this.$('#product_template_id').val();
        const product_id = this.$('input[name="product_id"]').val()
            || this.$('#product_variant_id').val();

        rpc('/website_estimated_delivery_time', {
            pin_number: search_value,
            product_template_id: product_template_id,
            product_id: product_id,
        }).then((result) => {
            if (result.product_base_availability === 'True' || result.website_base_availability === 'True') {
                this._showModal('AvailableModal');
                $('#message_to_show_available').text(result.available_message);
            } else {
                this._showModal('NotAvailableModal');
                $('#message_to_show_unavailable').text(result.unavailable_message);
            }
        });
    },
});
