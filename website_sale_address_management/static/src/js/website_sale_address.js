/** @odoo-module **/

import { CustomerAddress } from '@portal/interactions/address';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

/**
 * The address fields can be hidden from the form by the module settings, so
 * every access to an input has to tolerate a missing element.
 */
patch(CustomerAddress.prototype, {
    async _onChangeCountry(init = false) {
        const countryId = parseInt(this.addressForm.country_id?.value);
        if (!countryId) {
            return;
        }
        const data = await this.waitFor(rpc(
            `/my/address/country_info/${countryId}`,
            { address_type: this.addressType },
        ));

        const phoneInput = this.addressForm.phone;
        if (phoneInput) {
            phoneInput.placeholder = data.phone_code ? `+${data.phone_code}` : '';
        }

        // Populate the states and display them.
        const selectStates = this.addressForm.state_id;
        if (selectStates && (!init || selectStates.options.length === 1)) {
            // Do not reload the states at first loading (done in qweb).
            if (data.states.length || data.state_required) {
                // Empty the existing options, only keep the placeholder.
                selectStates.options.length = 1;
                // Create the new options and append them to the select.
                data.states.forEach((state) => {
                    const option = new Option(state[1], state[0]);
                    // Used by localizations.
                    option.setAttribute('data-code', state[2]);
                    selectStates.appendChild(option);
                });
                this._showInput('state_id');
            } else {
                selectStates.options.length = 1;
                this._hideInput('state_id');
            }
        }

        // Manage the fields order and visibility.
        if (data.fields) {
            const zipDiv = this._getInputDiv('zip');
            const cityDiv = this._getInputDiv('city');
            if (zipDiv && cityDiv) {
                if (data.zip_before_city) {
                    zipDiv.after(cityDiv);
                } else {
                    zipDiv.before(cityDiv);
                }
            }
            ['street', 'zip', 'city'].forEach((fname) => {
                if (data.fields.includes(fname)) {
                    this._showInput(fname);
                } else {
                    this._hideInput(fname);
                }
            });
        }

        // Remove the requirement on the previously required fields.
        this.addressForm.querySelectorAll(':required').forEach((element) => {
            if (
                !data.required_fields.includes(element.name)
                && !this.requiredFields.includes(element.name)
            ) {
                this._markRequired(element.name, false);
            }
        });
        data.required_fields.forEach((fieldName) => {
            this._markRequired(fieldName, true);
        });
    },

    _getInputDiv(name) {
        return this.addressForm[name]?.parentElement || null;
    },

    _showInput(name) {
        const div = this._getInputDiv(name);
        if (div) {
            div.style.display = '';
        }
    },

    _hideInput(name) {
        const div = this._getInputDiv(name);
        if (div) {
            div.style.display = 'none';
        }
    },
});
