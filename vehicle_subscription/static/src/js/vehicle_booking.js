/** @odoo-module **/

import publicWidget from 'web.public.widget';
import ajax from 'web.ajax';
publicWidget.registry.book = publicWidget.Widget.extend({
    selector: '#book_my_vehicle',
    events: {
        'click .redirect_back_with_data':'_onClickBack',
        'click .book_now':'_onClickBook',
        'click #with_fuel':'_onClickWithFuel',
        'click #without_fuel':'_onClickWithoutFuel',
        'change #extra_km':'_onChangeExtraKm',
        'click #full_subscription':'_onClickFullPayment',
        'click #monthly_subscription':'_onClickMonthlyPayment',
    },
   //Click function to book subscription
    _onClickBook: async function(ev){
        var checked=this.$('#checkbox_for_fuel')[0].checked
        var invoice_checked=this.$('#checkbox_for_invoice_type')[0].checked
        var customer_id = this.$('input[name="customer"]')[0].value
        var km = this.$('#extra_km')[0].value
        var vehicle_id = ev.currentTarget.firstChild.nextSibling.defaultValue
        await ajax.jsonRpc('/online/subscription/book', "call", {
            'vehicle': vehicle_id,
            'customer':customer_id,
            'checked':checked,
            'invoice':invoice_checked,
            'extra_km':km,
        }).then(function(result) {
            window.location.href="/next/vehicle/" +result.subscription_id;
        });
    },
     //Click function to set  price
    _onClickWithFuel: async  function(ev){
        this.$('#with_fuel .btn').css('background-color', 'red');
        this.$('#without_fuel .btn').css('background-color', '');
        this.$('#checkbox_for_fuel')[0].checked = true
        var km = this.$('#extra_km')[0].value
        var table = this.$('#vehicle_booking_table')[0];
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
                var current_price = row.cells[2].innerText
                var vehicle_id = row.cells[1].getAttribute('value')
                await  ajax.jsonRpc('/online/subscription/with/fuel', "call", {
                    'vehicle': vehicle_id,
                    'price':current_price,
                    'extra_km': km,
                })
                .then(function(result) {
                    row.cells[2].innerText = result
                })
            }
        }
    },
    //Click function to set  price without fuel
    _onClickWithoutFuel: async  function(ev){
        this.$('#without_fuel .btn').css('background-color', 'red');
        this.$('#with_fuel .btn').css('background-color', '');
        this.$('#checkbox_for_fuel')[0].checked = false
        var km = this.$('#extra_km')[0].value
        var table = this.$('#vehicle_booking_table')[0];
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
                var current_price = row.cells[2].innerText
                var vehicle_id = row.cells[1].getAttribute('value')
                await  ajax.jsonRpc('/online/subscription/without/fuel', "call", {
                'vehicle': vehicle_id,
                'price':current_price,
                'extra_km':km,
                })
                .then(function(result) {
                    row.cells[2].innerText = result
                })
            }
        }
    },
     //Change function to set price  using extra km
    _onChangeExtraKm: async function(ev){
        this.$('#checkbox_for_fuel')[0].checked = true
        this.$('#with_fuel .btn').css('background-color', 'red');
        this.$('#without_fuel .btn').css('background-color', '');
        var km = ev.currentTarget.value
        var table = this.$('#vehicle_booking_table')[0];
        for (var i = 1, row; row = table.rows[i]; i++) {
            for (var j = 1, col; col = row.cells[j]; j++) {
            var current_price = row.cells[2].innerText
            var vehicle_id = row.cells[1].getAttribute('value')
            await  ajax.jsonRpc('/online/subscription/with/fuel', "call", {
                'vehicle': vehicle_id,
                'price':current_price,
                'extra_km':km,
            })
            .then(function(result){
                row.cells[2].innerText = result
            })
            }
        }
    },
    //Click function
    _onClickFullPayment:function(ev){
        this.$('#checkbox_for_invoice_type')[0].checked = true
        this.$('#full_subscription .btn').css('background-color', 'red');
        this.$('#monthly_subscription .btn').css('background-color', '');
    },
    //Click function
    _onClickMonthlyPayment:function(ev){
        this.$('#checkbox_for_invoice_type')[0].checked = true
        this.$('#full_subscription .btn').css('background-color', '');
        this.$('#monthly_subscription .btn').css('background-color', 'red');
    },
    //Click function for previous page
    _onClickBack:function(ev){
        window.history.back();
    }
})
