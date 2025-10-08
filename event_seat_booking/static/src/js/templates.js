odoo.define('event_seat_booking.templates', function (require) {
    'use strict';
    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    publicWidget.registry.SeatBooking = publicWidget.Widget.extend({
        selector: '.main',
        events: {
            'click .seat-button': '_onSeatClick',
        },
        init: function () {
            this._super.apply(this, arguments);
            this.selectedSeats = [];
            this.seatCount = 0;
            this.totalPrice = 0;
            this.eventPrices = {}; // Dictionary to store event prices
            this.seatInformation = {};
        },
        //Seat onClick
        _onSeatClick: function (ev) {
            const seatButton = document.querySelector('.seat-button');
            const eventId = seatButton.getAttribute('data-event-id');
            var $target = $(ev.currentTarget);
            var ticketId = $target.data('event-id');
            var uniqueId = $target.data('seat-id');
            var seatCount = $target.hasClass('selected') ? 0 : 0;
            // Update the seat count for the ticket ID in the object
            this.eventPrices[ticketId] = (this.eventPrices[ticketId] || 0) + seatCount;
            var seatCount = 0;
            var rowNumber = $target.closest('.seats-column').find('.row-button').text().trim();
            var seatNumber = $target.text().trim();
            var eventName = $target.data('event-name');
            var eventPrice = parseFloat($target.data('event-price'));
            var selectedSeats = [];
            // Check if eventPrice is NaN (zero) and handle accordingly
            if (isNaN(eventPrice)) {
                eventPrice = 0;
            }
            //if reserved seat show alert

            if ($target.hasClass('reserved-seat')) {
               alert('This seat is already booked. Please choose another seat.');

                return; // Do nothing if the seat is confirmed
            }
            // Toggle the "selected" class on the seat-button
            $target.toggleClass('selected');
            // Show or hide the seat information in the selected-seats div based on the selected state
            var seatInfo = eventName + ' Seat' + '#' + 'R' + rowNumber + 'S' + seatNumber + ':' + eventPrice + "<br/>" ;
            var SeatID = 'Row' + rowNumber + 'Column' + seatNumber
            var uniqueRowKey = uniqueId + 'R' + rowNumber;
            var uniqueColumnKey = uniqueId + 'C' + seatNumber
            if ($target.hasClass('selected')) {
                // Add the uniqueId to the text input field
                var currentValue = this.$('#unique_column_id').val();
                var newValue = currentValue ? currentValue + ',' + uniqueId : uniqueId;
                this.$('#unique_column_id').val(newValue);
                // Add the uniqueRowKey to the row_number_id input field
                var currentRowNumberValue = this.$('#row_number_id').val();
                var newRowNumberValue = currentRowNumberValue ? currentRowNumberValue + ',' + uniqueRowKey : uniqueRowKey;
                this.$('#row_number_id').val(newRowNumberValue);
                // Add the seatNumber to the col_number_id input field
                var currentColNumberValue = this.$('#col_number_id').val();
                var newColNumberValue = currentColNumberValue ? currentColNumberValue + ',' + uniqueColumnKey : uniqueColumnKey;
                this.$('#col_number_id').val(newColNumberValue);
                this.seatCount += $target.hasClass('selected') ? 1 : 0;
                this.eventPrices[ticketId] = (this.eventPrices[ticketId] || 0) + 1;

                $('.seat-count').html(this.seatCount);
                this.totalPrice += $target.hasClass('selected') ? eventPrice : -eventPrice;
                $('.total').html(this.totalPrice);
                var seatDetail = $('<div>').addClass('seat-detail');
                seatDetail.append(seatInfo);
                $('.selected-seats').append(seatDetail);
            }
            else {
                // Handle the case where the seat is deselected
                var currentValue = $('#unique_column_id').val();
                var newValue = currentValue.split(',').filter(function(value) {
                    return value !== uniqueId;
                }).join(',');
                $('#unique_column_id').val(newValue)

                // Remove the seatNumber from the col_number_id input field
                var currentColNumberValue = $('#col_number_id').val();
                var newColNumberValue = currentColNumberValue.split(',').filter(function(value) {
                    return value !== uniqueColumnKey;
                }).join(',');
                $('#col_number_id').val(newColNumberValue);

                // Remove the uniqueRowKey from the row_number_id input field
                var currentRowNumberValue = $('#row_number_id').val();
                var newRowNumberValue = currentRowNumberValue.split(',').filter(function(value) {
                    return value !== uniqueRowKey;
                }).join(',');
                $('#row_number_id').val(newRowNumberValue);

                this.seatCount += $target.hasClass('selected') ? 0 : -1;
                this.eventPrices[ticketId] = (this.eventPrices[ticketId] || 0) + -1;
                $('.seat-count').html(this.seatCount);
                this.totalPrice -= eventPrice;
                $('.total').html(this.totalPrice);
                var seatToRemove = $('.seat-detail').eq(rowNumber - 1);
            seatToRemove.remove();
            }
             if (this.seatCount === 0) {
                $('.seat-detail').html('');

    }
            // Collect selected seat numbers
            this.$('.seat-button.selected').each(function () {
                var rowNumber = $(this).closest('.seats-column').find('.row-button').text();
                var seatNumber = $(this).text();
                selectedSeats.push("R" + rowNumber.trim() + "S" + seatNumber.trim() );
            });

             // Attach selected seat numbers to the register button
            $('#all_selected-seats').html(selectedSeats.join(', '));
            console.log(this.$('#all_selected-seats'),"the seats")
            var $nearestSelect = $target.closest('.separate-event').find('#selected_seats_input'); // Find the parent select tag
            console.log($nearestSelect,34432432)
            $nearestSelect.empty();
            for (var id in this.eventPrices) {
                if (this.eventPrices.hasOwnProperty(id)) {
                    var optionValue = id;  // Use the ticket ID as the option value
                    var optionText = optionValue + ': ' + this.eventPrices[id];
                        $nearestSelect.append($('<option>', {
                        value: this.eventPrices[id],
                        text: optionText,
                        selected: true
                    }));
                }
            }
        },

 });
    return publicWidget.registry.SeatBooking;
});
