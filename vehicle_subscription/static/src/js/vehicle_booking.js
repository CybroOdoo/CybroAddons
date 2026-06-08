/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { useService } from "@web/core/utils/hooks";
publicWidget.registry.book = publicWidget.Widget.extend({
    selector: '#book_my_vehicle',
    events: {
        'click .redirect_back_with_data': '_onClickBack',
        'click .book_now': '_onClickBook',
        'click #with_fuel': '_onClickWithFuel',
        'click #without_fuel': '_onClickWithoutFuel',
        'change #extra_km': '_onChangeExtraKm',
        'click #full_subscription': '_onClickFullPayment',
        'click #monthly_subscription': '_onClickMonthlyPayment',
    },
    init() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this._booked = false;
    },
    setup() {
        super.setup();
        this.book = useService("book");
    },
    async _onClickBook(ev) { //Click function to book subscription
        ev.preventDefault();
        ev.stopPropagation();
        // Prevent double booking
        if (this._booked) return;
        this._booked = true;
        // Disable all Book Now buttons immediately
        this.el.querySelectorAll('.book_now').forEach(btn => {
            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'not-allowed';
        });
        var checked = this.el.querySelector('#checkbox_for_fuel').checked
        var invoice_checked = this.el.querySelector('#checkbox_for_invoice_type').checked
        var customer_id = this.el.querySelector('input[name="customer"]').value
        var km = this.el.querySelector('#extra_km').value
        var monthly_subscription = this.el.querySelector('#checkbox_for_invoice_type').checked === true
        var vehicle_id = ev.currentTarget.firstChild.nextSibling.defaultValue
        // Read city, state, seating capacity and insurance type passed from the subscription form
        var cityEl = this.el.querySelector('#sub_city')
        var stateEl = this.el.querySelector('#sub_state_id')
        var seatingEl = this.el.querySelector('#sub_seating_capacity')
        var insuranceEl = this.el.querySelector('#sub_insurance_type')
        var city = cityEl ? cityEl.value : ''
        var state_id = stateEl ? stateEl.value : ''
        var seating_capacity = seatingEl ? seatingEl.value : 0
        var insurance_type_id = insuranceEl ? insuranceEl.value : ''
        await rpc('/online/subscription/book', {
            'vehicle': vehicle_id,
            'customer': customer_id,
            'checked': checked,
            'invoice': invoice_checked,
            'extra_km': km,
            'monthly_subscription': monthly_subscription,
            'city': city,
            'state_id': state_id,
            'seating_capacity': seating_capacity,
            'insurance_type_id': insurance_type_id,
        }).then(function (result) {
            window.location.href = "/next/vehicle/" + result.subscription_id;
        }).catch(() => {
            // Re-enable on error so user can retry
            this._booked = false;
            this.el.querySelectorAll('.book_now').forEach(btn => {
                btn.disabled = false;
                btn.style.opacity = '';
                btn.style.cursor = '';
            });
        });
    },
    async _onClickWithFuel(ev) { //Click function to set  price
        this.$('#with_fuel .btn').css('background-color', 'red');
        this.$('#without_fuel .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_fuel').checked = true
        var km = this.el.querySelector('#extra_km').value
        var table = this.el.querySelector('#vehicle_booking_table');
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
                var current_price = row.cells[2].innerText
                var vehicle_id = row.cells[1].getAttribute('value')
                await rpc('/online/subscription/with/fuel', {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                })
                    .then(function (result) {
                        row.cells[2].innerText = result
                    })
            }
        }
    },
    async _onClickWithoutFuel(ev) {//Click function to set  price without fuel
        this.$('#without_fuel .btn').css('background-color', 'red');
        this.$('#with_fuel .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_fuel').checked = true
        var km = this.el.querySelector('#extra_km').value
        var table = this.el.querySelector('#vehicle_booking_table');
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
                var current_price = row.cells[2].innerText
                var vehicle_id = row.cells[1].getAttribute('value')
                await rpc('/online/subscription/without/fuel', {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                })
                    .then(function (result) {
                        row.cells[2].innerText = result
                    })
            }
        }
    },
    async _onChangeExtraKm(ev) { //Change function to set price  using extra km
        var km = ev.currentTarget.value
        var table = this.el.querySelector('#vehicle_booking_table');
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
            var current_price = row.cells[2].innerText
                var vehicle_id = row.cells[1].getAttribute('value')
                var bgColor = this.$('#with_fuel .btn').css('background-color');
                var is_with_fuel = bgColor === 'rgb(255, 0, 0)' || bgColor === 'rgba(255, 0, 0, 1)'
                var rpc_url = "/online/subscription/without/fuel"
                if (is_with_fuel){
                    rpc_url = "/online/subscription/with/fuel"
                }
                await rpc(rpc_url, {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                })
                    .then(function (result) {
                        row.cells[2].innerText = result
                    })
            }
        }
    },
    _onClickFullPayment(ev) {//Click function
        this.$('#full_subscription .btn').css('background-color', 'red');
        this.$('#monthly_subscription .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_invoice_type').checked = false
    },
    _onClickMonthlyPayment(ev) {
        this.$('#full_subscription .btn').css('background-color', '');
        this.$('#monthly_subscription .btn').css('background-color', 'red');
        this.el.querySelector('#checkbox_for_invoice_type').checked = true
    },
    _onClickBack() {//Click function for previous page
        window.history.back();
    },
})