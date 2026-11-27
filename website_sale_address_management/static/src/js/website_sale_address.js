import { CustomerAddress } from '@portal/interactions/address';
import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';

/**
 * The address fields can be hidden from the form by the module settings, so
 * every access to an input has to tolerate a missing element.
 */
patch(CustomerAddress.prototype, {
    _getInputDiv(name) {
        return this.addressForm[name]?.parentElement || null;
    },

    _showInput(name) {
        const input = this.addressForm[name];
        if (input?.parentElement) {
            input.parentElement.style.display = '';
            input.disabled = false;
        }
    },

    _hideInput(name, clearValue = true) {
        const input = this.addressForm[name];
        if (input?.parentElement) {
            input.parentElement.style.display = 'none';
            if (clearValue) {
                input.disabled = true;
                input.value = '';
            }
        }
    },

    _setFieldChoices(name, data_list) {
        const selection = this.addressForm[name];
        if (!selection) {
            return;
        }
        super._setFieldChoices(...arguments);
    },

    /*
     * Update address layout depending on fields requirements and visibility,
     * safely tolerating missing/hidden fields (e.g. city or zip).
     */
    _updateAddressLayout() {
        const stateSelect = this.addressForm?.state_id;
        const hasStates = Boolean(stateSelect?.options && stateSelect.options.length > 1);
        const zipDiv = this._getInputDiv('zip');
        const zipVisible = Boolean(zipDiv && zipDiv.getClientRects().length > 0);

        const countryDiv = this._getInputDiv('country_id');
        const cityDiv = this._getInputDiv(this._getCityField());

        if (!hasStates && !zipVisible) {
            countryDiv?.classList.replace('col-lg-12', 'col-lg-6');
            if (cityDiv) {
                cityDiv.classList.remove('col-md-8', 'col-md-12');
                cityDiv.classList.add('col-lg-6');
            }
            if (countryDiv && cityDiv) {
                countryDiv.after(cityDiv);
            }
        } else {
            countryDiv?.classList.toggle('col-lg-6', hasStates);
            countryDiv?.classList.toggle('col-lg-12', !hasStates);

            if (cityDiv) {
                cityDiv.classList.remove('col-lg-6');
                cityDiv.classList.toggle('col-md-8', zipVisible);
                cityDiv.classList.toggle('col-md-12', !zipVisible);
            }
        }
    },

    async onChangeState() {
        if (!this.addressForm?.city_id) {
            return;
        }
        const countryId = parseInt(this.addressForm.country_id?.value);
        const stateId = parseInt(this.addressForm.state_id?.value);
        if (!countryId || !stateId) {
            return;
        }
        return super.onChangeState(...arguments);
    },

    async onChangeCountry() {
        const countryInput = this.addressForm.country_id;
        const countryId = countryInput ? parseInt(countryInput.value) : 0;
        if (!countryId) {
            return;
        }

        const data = await this.waitFor(
            rpc(`/my/address/country_info/${countryId}`, {
                address_type: this.addressType,
                use_delivery_as_billing: this.useDeliveryAsBilling,
            })
        );
        this.requiredFields = data.required_fields || [];

        if (this.addressForm.phone) {
            this.addressForm.phone.placeholder = data.phone_code || '';
        }
        const vatLabel = this._getInputLabel('vat');
        if (vatLabel) {
            vatLabel.textContent = data.vat_label || '';
        }

        // manage fields order / visibility
        if (data.address_fields) {
            const cityField = this._getCityField();
            const zipDiv = this._getInputDiv('zip');
            const cityDiv = this._getInputDiv(cityField);
            if (zipDiv && cityDiv) {
                if (data.zip_before_city) {
                    zipDiv.after(cityDiv);
                } else {
                    zipDiv.before(cityDiv);
                }
            }

            ['street', 'zip', 'state_id', 'city', 'city_id'].forEach((fname) => {
                if (data.address_fields.includes(fname)) {
                    if (data.selection && fname in data.selection) {
                        this._setFieldChoices(fname, data.selection[fname]);
                    }
                    if (!data.selection?.[fname]) {
                        this._showInput(fname);
                    }
                } else {
                    this._hideInput(fname);
                }
            });

            const countryCode = this._getSelectedCountryCode();
            this.addressForm.querySelectorAll('[data-country-code]').forEach((element) => {
                if (element.dataset.countryCode !== countryCode) {
                    this._hideInput(element.name);
                } else {
                    this._showInput(element.name);
                }
            });
        }

        // add requirement on new required fields
        data.required_fields?.forEach((fieldName) => {
            this._markRequired(fieldName, true);
        });
        this.addressForm.querySelectorAll(':required').forEach((element) => {
            // remove requirement on previously required fields
            if (
                !data.required_fields?.includes(element.name) &&
                !this.alwaysRequiredFields?.includes(element.name)
            ) {
                this._markRequired(element.name, false);
            }
        });

        this._updateAddressLayout();

        return data;
    },

    async onChangeCity() {
        const cityZipCode = this.addressForm.city_id?.selectedOptions?.[0]?.dataset?.zipcode;
        if (cityZipCode && this.addressForm.zip) {
            this.addressForm.zip.value = cityZipCode;
        }
    },

    async saveAddress(ev) {
        const origHttp = this.http;
        if (origHttp?.post) {
            const wrappedHttp = Object.create(origHttp);
            wrappedHttp.post = async (...args) => {
                const result = await origHttp.post(...args);
                if (result && !result.redirectUrl) {
                    result.invalid_fields = (result.invalid_fields || []).filter(
                        (fieldName) => Boolean(this.addressForm?.[fieldName])
                    );
                    result.messages = result.messages || [];
                }
                return result;
            };
            this.http = wrappedHttp;
        }
        try {
            return await super.saveAddress(...arguments);
        } finally {
            this.http = origHttp;
        }
    },
});
