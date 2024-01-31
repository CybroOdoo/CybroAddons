/** @odoo-module */
import publicWidget from 'web.public.widget';
let booked_table = []
publicWidget.registry.table_reservation_floor = publicWidget.Widget.extend({
    selector: '#tableContainer',
    events: {
        'click .card_table': '_onTableClick',
    },
    /**
    Select table for reservation
    **/
    _onTableClick: function () {
        var current_div_id = event.target.closest('.card_table')
        var rate = current_div_id.querySelector('#rate').innerText
        var count = this.$el.find('#count_table')[0];
        var amount = this.$el.find('#total_amount')[0];
        var booked = this.$el.find('#tables_input')[0];
        if (current_div_id.style.backgroundColor == 'green'){
            booked_table.splice(booked_table.indexOf(Number(current_div_id.id)), 1);
            current_div_id.style.backgroundColor = '#96ccd5';
            count.innerText = Number(count.innerText) - 1;
            amount.innerText = Number(amount.innerText) - Number(rate)
        }
        else{
            current_div_id.style.backgroundColor = 'green'
            count.innerText = Number(count.innerText) + 1;
            booked_table.push(Number(current_div_id.id))
            if (amount.innerText){
                amount.innerText = Number(rate) + Number(amount.innerText)
            }
            else{
                amount.innerText = Number(rate)
            }
        }
        booked.value  = booked_table
    },
});
