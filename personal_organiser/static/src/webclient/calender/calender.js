/** @odoo-module **/
import { Component, useState } from '@odoo/owl';
import { useService } from '@web/core/utils/hooks';

export class MiniCalendar extends Component {
    "Component to deal with calendar events"
    static template = 'personal_organiser.mini_calendar';

    setup() {
        this.orm = useService('orm');
        this.currentDate = new Date();
        this.state = useState({
            daysInMonth: [],        // Days in the current month with event flags
            selectedDate: null,      // Currently selected date
            selectedDayEvents: [],   // Events for the selected date
        });

        this.loadEvents();  // Load all events on component setup
    }

    // Method to load events from the backend
    async loadEvents() {
        const today = this.formatDate(new Date());  // Current date in YYYY-MM-DD format
        try {
            // Fetch events that start after today
            this.events = await this.orm.searchRead("calendar.event", [
                ["start_date", ">=", today],
            ]);
        } catch (error) {
            console.error("Error loading events:", error);
        }
        this.updateCalendar();  // Update the calendar once events are loaded
    }

    // Method to update the calendar view with event flags
    updateCalendar() {
        const year = this.currentDate.getFullYear();
        const month = this.currentDate.getMonth();
        const lastDate = new Date(year, month + 1, 0).getDate();

        // Generate days for the current month and check if they have events
        this.state.daysInMonth = Array.from({ length: lastDate }, (_, day) => {
            const currentDay = day + 1;
            const currentDate = new Date(year, month, currentDay);
            const hasEvent = this.events.some(event => {
                const eventDateString = event.start_date;
                const eventDate = new Date(`${eventDateString}T00:00:00`);
                const normalizedEventDate = new Date(eventDate.getFullYear(),
                    eventDate.getMonth(), eventDate.getDate());
                const normalizedCurrentDate = new Date(currentDate.getFullYear(),
                    currentDate.getMonth(), currentDate.getDate());
                return normalizedEventDate.getTime() === normalizedCurrentDate.getTime();
            });
            return {
                date: currentDate,
                hasEvent,
            };
        });
    }

    // Method to handle day selection and load events for the selected day
    async selectDay(day) {
        this.state.selectedDate = day.date;
        await this.fetchEventsForDay(day.date);  // Fetch events for the selected day
    }

    // Fetch events for the selected day
    async fetchEventsForDay(date) {
        try {
            const dateStr = this.formatDate(date); // Format the date as YYYY-MM-DD
            const events = await this.orm.searchRead('calendar.event', [
                ['start_date', '=', dateStr],  // Query events for this date
            ], ['name', 'description', 'start_date']);

            this.state.selectedDayEvents = events;  // Set the events for the selected day
        } catch (error) {
            console.error("Error fetching events:", error);
        }
    }

    // Helper function to format date as YYYY-MM-DD (handling timezone correctly)
    formatDate(date) {
        // Set the time to 00:00:00 for consistency
        date.setHours(0, 0, 0, 0);

        // Format the date to YYYY-MM-DD
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0'); // Months are 0-indexed
        const day = String(date.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }
}
