odoo.define('vehicle_subscription.book', function (require) {
    "use strict";
var publicWidget = require('web.public.widget');
const ajax = require('web.ajax');
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
   _onClickBook: async function(ev){ //Click function to book subscription
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
          _onClickWithFuel: async  function(ev){ //Click function to set  price
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
          _onClickWithoutFuel: async  function(ev){//Click function to set  price without fuel
                this.$('#checkbox_for_fuel')[0].checked = true
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
         _onChangeExtraKm: async function(ev){ //Change function to set price  using extra km
                var km = ev.currentTarget.value
                var table = this.$('#vehicle_booking_table')[0];
                 for (var i = 1, row; row = table.rows[i]; i++) {
                     for (var j = 1, col; col = row.cells[j]; j++) {
                         await  ajax.jsonRpc('/online/subscription/with/fuel', "call", {
                                'extra_km': km,
                            })
                            .then(function(result){
                                row.cells[1].innerText = result
                            })
                     }
                }
        },
        _onClickFullPayment:function(ev){//Click function
            this.$('#checkbox_for_invoice_type')[0].checked = true
        },
        _onClickMonthlyPayment:function(ev){//Click function
           this.$('#checkbox_for_invoice_type')[0].checked = true
        },
        _onClickBack:function(ev){//Click function for previous page
            window.history.back();
        }
})
})
