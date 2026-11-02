import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";

export class BookShow extends Interaction {
    /* Validates the chosen date and checks that the show plays that day. */
    static selector = ".book_show";
    dynamicContent = {
        "#choose_date": { "t-on-change": this.onDateChange },
    };

    async onDateChange(ev) {
        const dateInput = ev.currentTarget;
        if (!dateInput.value) {
            this.hideError(); // Cleared by the user: nothing to check
            return;
        }
        const selectedDate = new Date(dateInput.value);
        const currentDate = new Date();
        selectedDate.setHours(0, 0, 0, 0);
        currentDate.setHours(0, 0, 0, 0);
        if (selectedDate < currentDate) {
            dateInput.value = "";
            this.showError(_t("Please select today or a future date."));
        } else {
            this.hideError();
            await this.checkShowsOnDate(dateInput, selectedDate);
        }
    }

    async checkShowsOnDate(dateInput, date) {
        const formattedDate = new Date(date.getTime() - date.getTimezoneOffset() * 60000)
            .toISOString()
            .split("T")[0];
        const movieId = parseInt(this.el.querySelector("form").dataset.movieId);
        const result = await this.waitFor(
            rpc("/web/dataset/call_kw", {
                model: "movie.movie",
                method: "check_shows_on_date",
                args: [formattedDate, movieId],
                kwargs: {},
            })
        );
        if (!result) {
            dateInput.value = "";
            this.showError(_t("There are no shows on the selected date."));
        }
    }

    showError(message) {
        const errorEl = this.el.querySelector("#error_box");
        errorEl.textContent = message;
        errorEl.style.display = "";
    }

    hideError() {
        this.el.querySelector("#error_box").style.display = "none";
    }
}

registry.category("public.interactions").add("show_booking_management.BookShow", BookShow);
