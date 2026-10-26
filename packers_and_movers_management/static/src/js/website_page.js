import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class PackersAndMoversWidget extends Interaction {
    static selector = ".packers-and-movers-widget";
    dynamicContent = {
        "#check": {
            "t-on-click.prevent": this.onCheckClick,
        },
        "#next": {
            "t-on-click.prevent": this.onNextClick,
        },
        "#country_select": {
            "t-on-change": this.onCountryChange,
        },
        "form": {
            "t-on-submit": this.onFormSubmit,
        },
    };

    showError(message) {
        let alertEl = this.el.querySelector('.o_packers_alert');
        if (!alertEl) {
            alertEl = document.createElement('div');
            alertEl.className = 'o_packers_alert alert alert-danger my-2';
            alertEl.setAttribute('role', 'alert');
            const form = this.el.querySelector('form');
            if (form) {
                form.prepend(alertEl);
            } else {
                this.el.prepend(alertEl);
            }
        }
        alertEl.textContent = message;
        alertEl.classList.remove('d-none');
    }

    clearError() {
        const alertEl = this.el.querySelector('.o_packers_alert');
        if (alertEl) {
            alertEl.classList.add('d-none');
            alertEl.textContent = '';
        }
    }

    onCheckClick(ev) {
        this.clearError();
        var fromInput = this.el.querySelector('#from');
        var toInput = this.el.querySelector('#to');
        var from_location = fromInput ? fromInput.value.trim() : '';
        var to_location = toInput ? toInput.value.trim() : '';
        if (from_location !== '' && to_location !== '') {
            var loader = this.el.querySelector('#loader');
            var distance = this.el.querySelector('#distance');
            var details = this.el.querySelector('#details');
            if (loader) loader.classList.remove("d-none");
            rpc(`/geo/${from_location}/${to_location}`, {}).then((data) => {
                if (data && distance) {
                    distance.value = data;  // Set distance value
                }
                if (loader) loader.classList.add("d-none");
                if (details) details.classList.remove("d-none");
            }).catch(() => {
                if (loader) loader.classList.add("d-none");
                this.showError("Please enter a valid city");
            });
        } else {
            this.showError("Add Pickup City and Drop City");
        }
    }

    onNextClick(ev) {
        this.clearError();
        var date = this.el.querySelector('input[name="date"]')?.value;
        var truckType = this.el.querySelector('select[name="truck_type"]')?.value;
        var goodsType = this.el.querySelector('select[name="goods_type"]')?.value;
        var weight = this.el.querySelector('#weight')?.value;
        if (!date || !truckType || !goodsType || !weight) {
            this.showError("Please fill all required details (Date, Truck Type, Goods Type, and Weight)");
            return;
        }
        this.el.querySelector('#details')?.classList.add("d-none"); // Hide details section
        this.el.querySelector('#customer')?.classList.remove("d-none"); // Show customer section
    }

    onFormSubmit(ev) {
        this.clearError();
        var name = this.el.querySelector('input[name="name"]')?.value.trim();
        var city = this.el.querySelector('input[name="city"]')?.value.trim();
        var country = this.el.querySelector('#country_select')?.value;
        var state = this.el.querySelector('#state_select')?.value;
        if (!name || !city || !country || !state) {
            ev.preventDefault();
            this.showError("Please fill all required customer details (Name, City, Country, and State)");
        }
    }

    onCountryChange(ev) {
        var selectedCountryId = ev.target.value;
        var stateSelect = this.el.querySelector("#state_select");
        if (stateSelect) {
            var options = stateSelect.querySelectorAll("option");
            options.forEach(function (option) {
                var countryId = option.dataset.country;
                if (!countryId || countryId == selectedCountryId) {
                    option.style.display = "";
                } else {
                    option.style.display = "none";
                }
            });
        }
    }
}

registry
    .category("public.interactions")
    .add("packers_and_movers_management.packers_and_movers_widget", PackersAndMoversWidget);
