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
    },
    setup() {
        super.setup();
    },
    async _onClickBook(ev) { //Click function to book subscription
        var f_c = this.el.querySelector('#checkbox_for_fuel').value
        let fuel_choice = ''
        if (['with_fuel', 'without_fuel'].includes(f_c)) {
            fuel_choice = f_c
        }
        var checked = this.el.querySelector('#checkbox_for_fuel').checked
        var payment_type = this.el.querySelector('#checkbox_for_invoice_type').value || 'full'
        var customer_id = this.el.querySelector('input[name="customer"]').value
        var km = this.el.querySelector('#extra_km').value
        var vehicle_id = ev.currentTarget.firstChild.nextSibling.defaultValue
        var city = this.el.querySelector('input[name="city"]').value
        var state_id = this.el.querySelector('input[name="state_id"]').value
        var country_id = this.el.querySelector('input[name="country_id"]').value
        var seating_capacity = this.el.querySelector('input[name="seating_capacity"]').value
        await rpc('/online/subscription/book', {
            'vehicle': vehicle_id,
            'customer': customer_id,
            'checked': checked,
            'invoice_type': payment_type,
            'extra_km': km,
            'fuel_choice': fuel_choice,
            'city': city,
            'state_id': state_id,
            'country_id': country_id,
            'seating_capacity': seating_capacity,
        }).then(function (result) {
            window.location.href = "/next/vehicle/" + result.subscription_id;
        });
    },
    async _onClickWithFuel(ev) { //Click function to set price with fuel
        this.$('#with_fuel .btn').css('background-color', 'red');
        this.$('#without_fuel .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_fuel').checked = true;
        this.el.querySelector('#checkbox_for_fuel').value = 'with_fuel';
        var km = this.el.querySelector('#extra_km').value;
        var table = this.el.querySelector('#vehicle_booking_table');
        if (!table) return;
        for (var i = 1, row; row = table.rows[i]; i++) {
            if (!row.cells || row.cells.length < 3) continue;
            var current_price = row.cells[2].innerText;
            var vehicle_id = row.cells[1].getAttribute('value');
            if (vehicle_id) {
                const result = await rpc('/online/subscription/with/fuel', {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                });
                row.cells[2].innerText = result;
            }
        }
    },
    async _onClickWithoutFuel(ev) {//Click function to set price without fuel
        this.$('#without_fuel .btn').css('background-color', 'red');
        this.$('#with_fuel .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_fuel').checked = true;
        this.el.querySelector('#checkbox_for_fuel').value = 'without_fuel';
        var km = this.el.querySelector('#extra_km').value;
        var table = this.el.querySelector('#vehicle_booking_table');
        if (!table) return;
        for (var i = 1, row; row = table.rows[i]; i++) {
            if (!row.cells || row.cells.length < 3) continue;
            var current_price = row.cells[2].innerText;
            var vehicle_id = row.cells[1].getAttribute('value');
            if (vehicle_id) {
                const result = await rpc('/online/subscription/without/fuel', {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                });
                row.cells[2].innerText = result;
            }
        }
    },
    async _onChangeExtraKm(ev) { //Change function to set price using extra km
        var km = ev.currentTarget.value;
        var f_c = this.el.querySelector('#checkbox_for_fuel').value;
        var route = (f_c === 'without_fuel') ? '/online/subscription/without/fuel' : '/online/subscription/with/fuel';
        var table = this.el.querySelector('#vehicle_booking_table');
        if (!table) return;
        for (var i = 1, row; row = table.rows[i]; i++) {
            if (!row.cells || row.cells.length < 3) continue;
            var current_price = row.cells[2].innerText;
            var vehicle_id = row.cells[1].getAttribute('value');
            if (vehicle_id) {
                const result = await rpc(route, {
                    'vehicle': vehicle_id,
                    'price': current_price,
                    'extra_km': km,
                });
                row.cells[2].innerText = result;
            }
        }
    },
    _onClickFullPayment(ev) {//Click function
        this.$('#full_subscription .btn').css('background-color', 'red');
        this.$('#monthly_subscription .btn').css('background-color', '');
        this.el.querySelector('#checkbox_for_invoice_type').value = 'full';
        this.el.querySelector('#checkbox_for_invoice_type').checked = true;
    },
    _onClickMonthlyPayment(ev) {
        this.$('#full_subscription .btn').css('background-color', '');
        this.$('#monthly_subscription .btn').css('background-color', 'red');
        this.el.querySelector('#checkbox_for_invoice_type').value = 'monthly';
        this.el.querySelector('#checkbox_for_invoice_type').checked = true;
    },
    _onClickBack() {//Click function for previous page
        window.history.back();
    },
})
