import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

export class VenueBookingWidget extends Interaction {
    static selector = ".venue-booking-widget";
    dynamicContent = {
        "#next": {
            "t-on-click.prevent": this.onNextClick,
        },
    };

    async onNextClick(ev) {
        const fromDateInput = this.el.querySelector('#from_date');
        const toDateInput = this.el.querySelector('#to_date');
        const venueTypeSelect = this.el.querySelector('#venue_type');

        const start_date = fromDateInput ? fromDateInput.value : '';
        const end_date = toDateInput ? toDateInput.value : '';
        const venue_type = venueTypeSelect ? venueTypeSelect.value : '';

        if (!start_date || !end_date || !venue_type) {
            alert("Please fill out From Date, To Date, and Select Venue.");
            return;
        }

        if (new Date(start_date) >= new Date(end_date)) {
            alert("End Date must be after Start Date");
            return;
        }

        try {
            const result = await rpc('/booking/check_availability', {
                start_date: start_date,
                end_date: end_date,
                venue_id: parseInt(venue_type),
            });

            if (!result || !result.available) {
                alert("Venue is not available for the selected time range.");
            } else {
                const customerSection = this.el.querySelector('#customer');
                if (customerSection) customerSection.classList.remove("d-none");
                const nextBtn = this.el.querySelector('#next');
                if (nextBtn) nextBtn.classList.add("d-none");
            }
        } catch {
            // Venue availability check failed
        }
    }
}

registry
    .category("public.interactions")
    .add("venue_booking_management.venue_booking_widget", VenueBookingWidget);
