/** @odoo-module **/
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Handles the website salon booking page: submitting a new booking
 * request and refreshing the "Already Booked Chairs" section.
 *
 * NOTE: this used to be a publicWidget (jQuery-based). publicWidget and
 * jQuery were both removed from this Odoo version's frontend in favour
 * of the lightweight Interaction framework - hence the rewrite below.
 * Same behaviour, plain DOM APIs instead of jQuery.
 */
export class SalonManagement extends Interaction {
    static selector = ".chair_booking";

    dynamicContent = {
        "#send_button": { "t-on-click": () => this.onClickSend() },
        "#check_button": { "t-on-click": () => this.onClickCheckButton() },
        "#date": { "t-on-change": () => this.onBookingDateChange() },
    };

    /**
     * On load, default the "Already Booked Chairs" date picker to today
     * and refresh that section using the visitor's real (browser
     * detected) timezone. The initial server-rendered version of this
     * section is computed using the logged-in user's timezone which,
     * for an anonymous website visitor, is empty and silently falls
     * back to UTC - so the "today" it shows can be off by several
     * hours from the visitor's actual today. Re-running the same query
     * client-side with the correct timezone fixes that as soon as the
     * page loads, with no visible flash for the vast majority of
     * visitors whose timezone matches the salon's.
     */
    start() {
        const checkDateInput = this.el.querySelector("#check_date");
        const today = new Date();
        const iso = today.getFullYear() + "-" +
            String(today.getMonth() + 1).padStart(2, "0") + "-" +
            String(today.getDate()).padStart(2, "0");
        if (checkDateInput && !checkDateInput.value) {
            checkDateInput.value = iso;
        }
        this._loadBookingsForDate(iso);
    }

    /** Minimal HTML-escaping helper. **/
    _escape(text) {
        const div = document.createElement("div");
        div.textContent = text == null ? "" : String(text);
        return div.innerHTML;
    }

    /** Best-effort detection of the visitor's own timezone so the date
        & time they type on the booking form is interpreted the way they
        mean it, instead of defaulting to UTC for anonymous visitors. **/
    _getClientTz() {
        try {
            return Intl.DateTimeFormat().resolvedOptions().timeZone || "";
        } catch (e) {
            return "";
        }
    }

    /** Show a message to the visitor in the form's message area. **/
    _showMessage(message) {
        const box = this.el.querySelector("#salon_form_message");
        if (box) {
            box.textContent = message;
            box.classList.remove("d-none");
        }
    }

    /** Hide the message area. **/
    _clearMessage() {
        const box = this.el.querySelector("#salon_form_message");
        if (box) {
            box.textContent = "";
            box.classList.add("d-none");
        }
    }

    /** Function to check validation cases and create booking
        while click send button from booking page(website). **/
    onClickSend() {
        const root = this.el;
        this._clearMessage();
        const name = root.querySelector("#name").value;
        const date = root.querySelector("#date").value;
        const time = root.querySelector("#time").value;
        const phone = root.querySelector("#phone").value;
        const email = root.querySelector("#email").value;
        const checkedServices = root.querySelectorAll(".check_box_salon:checked");
        const chair = parseInt(root.querySelector("#chair").value, 10);
        const list_service = [];
        checkedServices.forEach((el) => {
            list_service.push(parseInt(el.getAttribute("service-id"), 10));
        });
        if (name == "" || date == "" || time == "" || phone == "" || email == "" || list_service.length == 0 || !chair) {
            this._showMessage("All fields are mandatory");
            return;
        }
        // Phone validation: 7 to 15 digits only
        const phonePattern = /^[0-9]{7,15}$/;
        if (!phonePattern.test(phone)) {
            this._showMessage("Invalid phone number. Please enter 7 to 15 digits only (e.g. 9991212345).");
            return;
        }
        // Email validation
        const emailPattern = /^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(email)) {
            this._showMessage("Invalid email address. Please enter a valid email (e.g. example@gmail.com).");
            return;
        }
        const colonIndex = time.indexOf(":");
        const hours = time.substring(0, colonIndex);
        const minutes = time.substring(colonIndex + 1);
        const colon = time[colonIndex];
        if (isNaN(hours) || isNaN(minutes) || colon != ":") {
            this._showMessage("Select a valid Time");
            return;
        }
        const time_left = parseInt(hours);
        const time_right = parseInt(minutes);
        if (!((time_left < 24) && (time_right < 60) && (time_left >= 0) && (time_right >= 0))) {
            this._showMessage("Select a valid time");
            return;
        }
        const sendButton = root.querySelector("#send_button");
        sendButton.disabled = true;
        rpc("/page/salon_details", {
            name: name,
            date: date,
            salon_time: time,
            phone: phone,
            email: email,
            chair: chair,
            service_list: list_service,
            tz: this._getClientTz(),
        }).then((data) => {
            if (data.result == true) {
                window.location.href = "/page/salon_management/salon_booking_thank_you";
            } else {
                // The chair became unavailable for the chosen
                // time (e.g. someone else just booked it).
                sendButton.disabled = false;
                this._showMessage(data.error || "This chair is no longer available at the selected time. Please pick another chair or time.");
            }
        }).catch(() => {
            sendButton.disabled = false;
            this._showMessage("Booking failed. Please check your details and try again.");
        });
    }

    /** When the visitor changes the booking date, show a quick,
        purely informational summary of how busy each chair already is
        that day, so they can pick a likely-free chair before typing a
        time and submitting. The server still re-checks availability on
        submit, so this is a helper, not the source of truth. **/
    onBookingDateChange() {
        const hint = this.el.querySelector("#chair_availability_hint");
        const date = this.el.querySelector("#date").value;
        if (!hint) {
            return;
        }
        if (!date) {
            hint.textContent = "Pick a date to see how busy each chair is that day.";
            return;
        }
        hint.textContent = "Checking chair availability...";
        rpc("/page/salon_check_date", {
            check_date: date,
            tz: this._getClientTz(),
        }).then((order_details) => {
            const parts = [];
            for (const chairId in order_details) {
                const info = order_details[chairId];
                if (!info.orders || !info.orders.length) {
                    continue;
                }
                const times = info.orders.map((o) => o.start_time_only + "-" + o.end_time_only).join(", ");
                parts.push(info.name + ": " + info.orders.length +
                    (info.orders.length === 1 ? " booking" : " bookings") +
                    (times ? " (" + times + ")" : ""));
            }
            hint.textContent = parts.length ?
                ("On this date - " + parts.join(" | ")) :
                "No existing bookings on this date yet.";
        }).catch(() => {
            hint.textContent = "Select the date & time based on chair availability.";
        });
    }

    /** Website function to check already booked chairs and details **/
    onClickCheckButton() {
        const check_date = this.el.querySelector("#check_date").value;
        if (check_date == "") {
            this._showMessage("Fill the Field");
            return;
        }
        this._loadBookingsForDate(check_date);
    }

    /** Fetches the salon orders for the given date and (re)renders the
        "Already Booked Chairs and Details" grid. Shared by the initial
        page load (today, in the visitor's real timezone) and the manual
        "Check" button. **/
    _loadBookingsForDate(check_date) {
        rpc("/page/salon_check_date", {
            check_date: check_date,
            tz: this._getClientTz(),
        }).then((order_details) => {
            this._renderBookingChairs(order_details);
            const date_field = this.el.querySelector("#searched_date");
            if (date_field) {
                date_field.textContent = "DATE : " + check_date;
            }
        }).catch(() => {
            this._showMessage("Could not load the bookings. Please try again.");
        });
    }

    /** Builds the per-chair cards for #booking_chair_div. Kept as valid
        (table > thead/tbody, no stray <div> inside <table>) markup -
        browsers silently move invalid table content out of the table
        during parsing, which is what made this section render broken
        after a manual date check. **/
    _renderBookingChairs(order_details) {
        const container = this.el.querySelector("#booking_chair_div");
        if (!container) {
            return;
        }
        let cards = "";
        for (const chairId in order_details) {
            const info = order_details[chairId];
            let rows = "";
            for (let i = 0; i < info.orders.length; i++) {
                const order = info.orders[i];
                rows += "<tr><td>" + order.number + "</td><td>" +
                    order.start_time_only + "</td><td>" +
                    order.end_time_only + "</td></tr>";
            }
            if (!rows) {
                rows = '<tr><td colspan="3" class="salon-empty-row">No bookings for this date</td></tr>';
            }
            cards += '<div class="col-lg-4 col-md-6 mb-3">' +
                '<div class="salon-chair-card">' +
                '<div class="salon-chair-card__name"><i class="fa fa-user-circle-o"></i> ' +
                this._escape(info.name) + "</div>" +
                '<div class="salon-chair-card__body">' +
                '<table class="table table-sm salon-order-table mb-0">' +
                "<thead><tr><th>Order No.</th><th>Start</th><th>End</th></tr></thead>" +
                "<tbody>" + rows + "</tbody>" +
                "</table></div></div></div>";
        }
        if (!cards) {
            cards = '<div class="col-12"><div class="salon-empty-state">' +
                "No chairs are open for booking, or none have bookings on this date.</div></div>";
        }
        container.innerHTML = cards;
    }
}

registry.category("public.interactions").add("salon_management.SalonManagement", SalonManagement);
