/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.InsuranceRequest = publicWidget.Widget.extend({
    selector: '.ins-main-body',
    events: {
        "change .date-of-birth": '_onDateOfBirthChange',  // bind onchange event
    },

    // Triggered when DOB changes
    _onDateOfBirthChange: function (ev) {
        this._calculateAge();
    },

    _calculateAge: function () {
        const dobInput = document.getElementById('date_of_birth');  // correct id
        const ageInput = document.getElementById('age');

        if (dobInput && ageInput) {
            const dobValue = dobInput.value;
            if (dobValue) {
                const today = new Date();
                const birthDate = new Date(dobValue);
                let age = today.getFullYear() - birthDate.getFullYear();
                const monthDifference = today.getMonth() - birthDate.getMonth();

                // Adjust age if the birthday hasn't occurred yet this year
                if (monthDifference < 0 || (monthDifference === 0 && today.getDate() < birthDate.getDate())) {
                    age--;
                }

                ageInput.value = age;
            } else {
                ageInput.value = '';
            }
        }
    },
});

export default publicWidget.registry.InsuranceRequest;
