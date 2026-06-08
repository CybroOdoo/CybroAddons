/** @odoo-module */
import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.websiteSlotTimeHours = publicWidget.Widget.extend({
    selector: '.slot-time-div',
    events: {
        'change input[type="radio"][name="slot_hour"]': '_onSlotTime',
    },
    /**
     * Event handler for slot hour radio button selection.
     *
     * When a user selects a different slot hour, this function sends the selected
     * value to the server via RPC (`/shop/cart/get_option`). The server responds
     * with a list of options to be populated in the delivery slot <select> (#slot_id).
     * Existing options in the delivery slot select are removed before adding new ones.
     *
     * @param {Event} ev - The change event triggered by selecting a radio button.
     */
    _onSlotTime: function(ev) {
        var selected_option = $("input[type='radio'][name='slot_hour']:checked").val();
        rpc('/shop/cart/get_option', {
            'selected_option': selected_option,
        }).then(function(result) {
            // Target the specific delivery slot <select> with id="slot_id"
            const deliverySelect = document.getElementById('slot_id');
            if (deliverySelect) {
                // Clear existing options
                deliverySelect.innerHTML = '';
                // Add placeholder option
                let placeholderOption = new Option('Select a slot', '');
                deliverySelect.add(placeholderOption);
                // Add new options
                result.forEach((item) => {
                    let newOption = new Option(item[1], item[0]);
                    deliverySelect.add(newOption, undefined);
                });
                // Ensure no option is selected by default
                deliverySelect.selectedIndex = 0; // Select the placeholder
                const lineId = $(ev.currentTarget).attr('data-line-id'); // Get the line ID if needed
            }
        });
    },
});