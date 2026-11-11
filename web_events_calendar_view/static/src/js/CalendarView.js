import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { renderToFragment } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";
import { loadCSS, loadJS } from "@web/core/assets";

export class CustomCalendar extends Interaction {
    static selector = ".s_event_calendar_list";

    async start() {
        const amountEl = this.el.querySelector(".js_amount");
        this.defaultAmount = Number(amountEl?.textContent) || 4;
        const events = await this.loadEvents(null, this.defaultAmount);
        this.renderList(events);
        await this._loadFullCalendar();
    }

    async _loadFullCalendar() {
        await Promise.all([
            loadCSS("https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.css"),
            loadJS("https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.js"),
        ]);
        await this._initializeCalendar();
    }

    async _initializeCalendar() {
        const calendarEl = this.el.querySelector(".s_event_calendar");
        if (!calendarEl || !window.FullCalendar) {
            return;
        }

        const events = await rpc("/web_events_calendar_view/events", {});

        this.calendar = new window.FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            events: events,
            dateClick: (info) => this.handleDateClick(info),
        });
        this.calendar.render();
    }

    async handleDateClick(info) {
        this.selectedDate = info.dateStr;

        const prev = this.el.querySelector(".fc-selected");
        if (prev) {
            prev.classList.remove("fc-selected");
            prev.style.backgroundColor = "";
        }

        info.dayEl.classList.add("fc-selected");
        info.dayEl.style.backgroundColor = "#1b918b";

        const amountEl = this.el.querySelector(".js_amount");
        this.defaultAmount = Number(amountEl?.textContent) || 4;
        const events = await this.loadEvents(info.dateStr, this.defaultAmount);
        this.renderList(events);
    }

    renderList(events) {
        const listEl = this.el.querySelector(".s_event_list");
        if (!listEl) {
            return;
        }
        listEl.innerHTML = "";
        listEl.append(renderToFragment("web_events_calendar_view.list", { events: events || [] }));
    }

    loadEvents(day, limit) {
        return rpc("/web_events_calendar_view/events_for_day", { day: day, limit: limit });
    }

    destroy() {
        if (this.calendar) {
            this.calendar.destroy();
            this.calendar = null;
        }
        super.destroy();
    }
}

registry
    .category("public.interactions")
    .add("web_events_calendar_view.custom_calendar", CustomCalendar);