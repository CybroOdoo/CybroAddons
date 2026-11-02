import { registry } from "@web/core/registry";

function setDate(daysFromToday) {
    return function ({ anchor }) {
        const date = new Date();
        date.setDate(date.getDate() + daysFromToday);
        const pad = (n) => String(n).padStart(2, "0");
        anchor.value = `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
        anchor.dispatchEvent(new Event("change", { bubbles: true }));
    };
}

registry.category("web_tour.tours").add("show_booking_tour", {
    steps: () => [
        {
            content: "Wait for the frontend JavaScript to be ready",
            trigger: "body[is-ready='true']",
        },
        {
            content: "The running show is listed: open its booking page",
            trigger: "a[href^='/book_now/']",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "BookShow interaction: a past date is refused client side",
            trigger: ".book_show #choose_date",
            run: setDate(-2),
        },
        {
            content: "Error shown and the date cleared",
            trigger: ".book_show #error_box:visible:contains('future')",
        },
        {
            content: "BookShow interaction: a date without show is refused after the RPC",
            trigger: ".book_show #choose_date",
            run: setDate(400),
        },
        {
            content: "The check_shows_on_date RPC answered: no show that day",
            trigger: ".book_show #error_box:visible:contains('no shows')",
        },
        {
            content: "A date inside the show period is accepted",
            trigger: ".book_show #choose_date",
            run: setDate(1),
        },
        {
            content: "Give the check_shows_on_date RPC time to (wrongly) clear the date",
            trigger: ".book_show #error_box:not(:visible)",
            async run() {
                await new Promise((resolve) => setTimeout(resolve, 700));
            },
        },
        {
            content: "The date is still there: submit the form",
            trigger: ".book_show #choose_date:not(:value(''))",
        },
        {
            content: "Select seats",
            trigger: ".book_show button[type='submit']",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "SelectSeat interaction: the seat chart is displayed",
            trigger: ".seat-selection .seat-label",
        },
        {
            content: "Confirm button is hidden until a seat is chosen",
            trigger: ".seat-selection .button-container:not(:visible)",
        },
        {
            content: "Pick a seat",
            trigger: ".seat-selection label[for='seat-3-1']",
            run: "click",
        },
        {
            content: "The confirm button and the counter appear",
            trigger: ".seat-selection .button-container:visible",
        },
        {
            content: "The counter shows one seat",
            trigger: ".seat-selection .seat-demo-selected:contains('1')",
        },
        {
            content: "Switch to the second time slot (update_seats RPC)",
            trigger: ".seat-selection .time-slot-btn:not(.active)",
            run: "click",
        },
        {
            content: "The sidebar time slot follows",
            trigger: ".sidebar .sidebar_timeslot:contains('09:00 PM')",
        },
        {
            content: "A seat already booked for that slot is now disabled",
            trigger: ".seat-selection input#seat-2-2:disabled:checked:not(:visible)",
        },
        {
            // v19 behaviour, kept: the seats are unticked and the counter reset, but the
            // confirm button is only re-evaluated on the next seat change.
            content: "The previous selection was reset",
            trigger: ".seat-selection .seat-demo-selected:contains('0')",
        },
        {
            content: "Pick a seat for the new slot",
            trigger: ".seat-selection label[for='seat-3-2']",
            run: "click",
        },
        {
            content: "Confirm the booking",
            trigger: ".seat-selection .button-container:visible .confirm_booking",
            run: "click",
            expectUnloadPage: true,
        },
        {
            content: "Redirected to the invoice to pay",
            trigger: ".o_portal_invoice_sidebar",
        },
    ],
});
