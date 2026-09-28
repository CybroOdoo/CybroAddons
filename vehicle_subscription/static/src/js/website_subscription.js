/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { Dialog } from "@web/core/dialog/dialog";

import { useService } from "@web/core/utils/hooks";
publicWidget.registry.Location = publicWidget.Widget.extend({
    selector: '#whole_sub',
    events: {
        'click #location_id': '_onLocationClick',
        'click #dismiss': '_onCloseClick',
        'click #next': '_onNextClick'
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
    },
    setup() {
        super.setup();
        //        this.location = useService("location");
    },
    _onLocationClick() {
        var location = this.el.querySelector('#location_temp');
        location.style.display = 'block';
    },
    // Click function of close button state and city is appended in location field.
    _onCloseClick(ev) {
        var state = this.el.querySelector("#state_id");
        var city = this.el.querySelector('#city_id');
        if (!state.reportValidity() || !city.reportValidity()) {
            ev.preventDefault();
            ev.stopPropagation();
            return;
        }
        var location = this.el.querySelector('#location_temp');
        this.el.querySelector('#location_id').value = state.selectedOptions[0].text + ',' + city.value;
        location.style.display = 'none';
    },
    // date validation in Subscription form.
    _onNextClick(e) {
        var startInput = this.el.querySelector('#start_date');
        var endInput = this.el.querySelector('#end_date');
        if (startInput && endInput) {
            startInput.setCustomValidity('');
            endInput.setCustomValidity('');
            if (startInput.value && endInput.value && startInput.value > endInput.value) {
                e.preventDefault();
                endInput.setCustomValidity('The Start Date must be earlier than the End Date.');
                endInput.reportValidity();
            }
        }
    }
})
