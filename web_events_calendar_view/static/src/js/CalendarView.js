/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { renderToFragment } from "@web/core/utils/render";
import { rpc } from "@web/core/network/rpc";

publicWidget.registry.CustomCalendar = publicWidget.Widget.extend({
    selector: '.s_event_calendar_list',

    start: function () {
        this.defaultAmount = Number(this.$(".js_amount").html()) || 4;
        this.loadEvents(null, this.defaultAmount).then(this.renderList.bind(this));
        this._load_fullcalendar();
    },

    _load_fullcalendar: function () {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.css';
        document.head.appendChild(link);

        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/fullcalendar@5.10.0/main.min.js';
        script.onload = this._initialize_calendar.bind(this);
        document.body.appendChild(script);
    },

    async _initialize_calendar() {
        const calendarEl = document.querySelector('.s_event_calendar');
        if (!calendarEl) return;

        const events = await rpc("/web_events_calendar_view/events", {});

        new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            events: events,
            dateClick: (info) => this.handleDateClick(info),
        }).render();
    },

    handleDateClick(info) {
        this.selected_date = info.dateStr;

        const prev = document.querySelector('.fc-selected');
        if (prev) {
            prev.classList.remove('fc-selected');
            prev.style.backgroundColor = '';
        }

        info.dayEl.classList.add('fc-selected');
        info.dayEl.style.backgroundColor = '#1b918b';

        this.defaultAmount = Number(document.querySelector(".js_amount").innerHTML) || 4;
        this.loadEvents(info.dateStr, this.defaultAmount).then(this.renderList.bind(this));
    },

    renderList: function (events) {
        const listEl = document.querySelector('.s_event_list');
        if (!listEl) return;
        listEl.innerHTML = '';
        listEl.append(renderToFragment('web_events_calendar_view.list', { events }));
    },

    loadEvents: function (day, limit) {
        return rpc("/web_events_calendar_view/events_for_day", { day: day, limit: limit });
    },
});