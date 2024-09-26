/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.selectSeat = publicWidget.Widget.extend({
    /* Extending widget and creating selectSeat */
    selector: '.seat-selection',
    events: {
        'change .seat-checkbox': 'UpdateSeatCount',
        'click .time-slot-btn': 'UpdateSeatChart',
    },
    UpdateSeatCount: function (ev) {
        /* Function for hiding and showing the
         confirm button based on selecting seats. */
        var checked_seats = this.$el.find('.seat-checkbox:checked:not(:disabled)')
        if (checked_seats.length > 0){
            this.$el.find('.button-container').show()
            this.$el.find('.selected-seats').show()
            this.$el.find('.seat-demo-selected')[0].innerText = checked_seats.length
        }else{
            this.$el.find('.button-container').hide()
            this.$el.find('.selected-seats').hide()
        }
    },
    UpdateSeatChart: function(ev){
        /* Function for updating the seat chart and side bar contents
         based on the clicking the time slots */
        this.$el.find('.time-slot-btn').removeClass('active');
        ev.currentTarget.classList.add("active")
        this.$el.find('.seat-demo-selected')[0].innerText = 0;
        const screenId = this.$el.find('input[name="screen_id"]').val();
        const timeSlotId = ev.currentTarget.dataset.timeSlotId
        const booking_date = this.$el.find('input[name="booking_date"]').val();
        this.$el.find('input[name="time_slot_id"]').val(timeSlotId);
        jsonrpc("/web/dataset/call_kw", {
            model: 'movie.movie',
            method: 'update_seats',
            args: [screenId,timeSlotId,booking_date],
            kwargs: {}
        }).then((result) => {
            this.$el.siblings().find('.sidebar_timeslot')[0].innerText = result.time_slot;
            this.$el.siblings().find('.seat-demo-booked')[0].innerText = result.booked_seats_count;
            this.$el.siblings().find('.seat-demo-available')[0].innerText = result.available_seats_count;
            var bookedSeats = result.booked_seats;
            this.$el.find('.seat-checkbox').each(function() {
                var seatId = this.value;
                if (bookedSeats.includes(seatId)) {
                    this.checked = true;
                    this.disabled = true;
                } else {
                    this.checked = false;
                    this.disabled = false;
                }
            });
        })
    },
})
