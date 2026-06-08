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
    // Click function of close button: state and city are appended in location field
    // and also written to hidden inputs so they are submitted with the form.
    _onCloseClick(ev) {
        var location = this.el.querySelector('#location_temp');
        var city = this.el.querySelector('#city_id').value;
        var state = this.el.querySelector("#state_id");
        var stateName = state.selectedOptions[0].text;
        var stateVal = state.value;
        // Update visible location label
        this.el.querySelector('#location_id').value = stateName + (city ? ', ' + city : '');
        // Write values into hidden inputs so the form POST carries them
        var stateHidden = this.el.querySelector('#state_hidden');
        var stateNameHidden = this.el.querySelector('#state_name_hidden');
        var cityHidden = this.el.querySelector('#city_hidden');
        if (stateHidden) stateHidden.value = stateVal;
        if (stateNameHidden) stateNameHidden.value = stateName;
        if (cityHidden) cityHidden.value = city;
        location.style.display = 'none';
    },
    // date validation in Subscription form.
    _onNextClick(e) {
        var start = this.el.querySelector('#start_date').value;
        var end = this.el.querySelector('#end_date').value;
        if (start > end) {
            e.preventDefault();
            alert('The Start Date must be earlier than the End Date!!!!!!!!!');
        }
    }
})