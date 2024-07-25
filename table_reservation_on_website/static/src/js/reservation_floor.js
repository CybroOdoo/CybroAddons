/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
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
        this.$el.find('.submit_button').prop('disabled', false);
        var current_div_id = event.target.closest('.card_table')
        var rateElement = current_div_id.querySelector('#rate');
        var countElement = this.$el.find('#count_table')[0];
        var amountElement = this.$el.find('#total_amount')[0];
        var bookedElement = this.$el.find('#tables_input')[0];
        var rate = rateElement ? rateElement.innerText : 0;
        if (current_div_id.style.backgroundColor == 'green'){
            booked_table.splice(booked_table.indexOf(Number(current_div_id.id)), 1);
            current_div_id.style.backgroundColor = '#96ccd5';
            if (countElement) {
                var countText = countElement.innerText.trim();
                var count = countText !== '' ? Number(countText) : 0;
                countElement.innerText = count > 0 ? count - 1 : 0;
            }
            if (amountElement) {
                amountElement.innerText = Number(amountElement.innerText) - Number(rate);
            }
        }
        else{
            current_div_id.style.backgroundColor = 'green'
            if (countElement) {
                var countText = countElement.innerText.trim();
                var count = countText !== '' ? Number(countText) : 0;
                countElement.innerText = count + 1;
            }
            booked_table.push(Number(current_div_id.id))
            if (amountElement) {
                if (amountElement.innerText) {
                    amountElement.innerText = Number(rate) + Number(amountElement.innerText);
                } else {
                    amountElement.innerText = Number(rate);
                }
            }
        }
        if (bookedElement) {
            bookedElement.value = booked_table;
        }
        if (this.$el.find('#count_table')[0]) {
            if (Number(this.$el.find('#count_table')[0].innerText.trim()) == 0){
                this.$el.find('.submit_button').prop('disabled', true);
            }
            else{
                this.$el.find('.submit_button').prop('disabled', false);
            }
        }
    },
});
