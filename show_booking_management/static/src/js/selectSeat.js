import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class SelectSeat extends Interaction {
    /* Seat chart: confirm button, seat counter and time slot switching. */
    static selector = ".seat-selection";
    dynamicContent = {
        ".seat-checkbox": { "t-on-change": this.onSeatChange },
        ".time-slot-btn": { "t-on-click": this.onTimeSlotClick },
    };

    /** The details sidebar is rendered next to the seat chart, not inside it. */
    get sidebar() {
        return this.el.parentElement;
    }

    onSeatChange() {
        /* Show or hide the confirm button according to the selected seats. */
        const checkedSeats = this.el.querySelectorAll(".seat-checkbox:checked:not(:disabled)");
        const hasSeats = checkedSeats.length > 0;
        this.el.querySelector(".button-container").style.display = hasSeats ? "" : "none";
        this.el.querySelector(".selected-seats").style.display = hasSeats ? "" : "none";
        if (hasSeats) {
            this.el.querySelector(".seat-demo-selected").innerText = checkedSeats.length;
        }
    }

    async onTimeSlotClick(ev) {
        /* Reload the seat chart and the sidebar for the clicked time slot. */
        this.el.querySelectorAll(".time-slot-btn").forEach((btn) => btn.classList.remove("active"));
        ev.currentTarget.classList.add("active");
        this.el.querySelector(".seat-demo-selected").innerText = 0;
        const screenId = this.el.querySelector('input[name="screen_id"]').value;
        const timeSlotId = ev.currentTarget.dataset.timeSlotId;
        const bookingDate = this.el.querySelector('input[name="booking_date"]').value;
        this.el.querySelector('input[name="time_slot_id"]').value = timeSlotId;
        const result = await this.waitFor(
            rpc("/web/dataset/call_kw", {
                model: "movie.movie",
                method: "update_seats",
                args: [screenId, timeSlotId, bookingDate],
                kwargs: {},
            })
        );
        this.sidebar.querySelector(".sidebar_timeslot").innerText = result.time_slot;
        this.sidebar.querySelector(".seat-demo-booked").innerText = result.booked_seats_count;
        this.sidebar.querySelector(".seat-demo-available").innerText = result.available_seats_count;
        this.el.querySelectorAll(".seat-checkbox").forEach((seat) => {
            const isBooked = result.booked_seats.includes(seat.value);
            seat.checked = isBooked;
            seat.disabled = isBooked;
        });
    }
}

registry.category("public.interactions").add("show_booking_management.SelectSeat", SelectSeat);
