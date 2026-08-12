/** @odoo-module **/
import { Component, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class PersonalOrganizer extends Component {
    static template = 'personal_organiser.task';

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            newTask: '',
            date: '',
            tasks: [],
        });
        this.fetchUserData();
    }

    async fetchUserData() {
        try {
            const tasks = await this.orm.searchRead("personal.organiser", [
                ["user_id", "=", user.userId]
            ], ['task_title', 'date', 'id']);

            // Ensure dates are properly formatted
            this.state.tasks = tasks.map(task => ({
                ...task,
                date: task.date ? task.date.split(' ')[0] : '', // Extract just the date part
            }));

            // Sort tasks by date
            this.state.tasks.sort((a, b) => new Date(a.date) - new Date(b.date));
        } catch (error) {
            console.error('Error fetching user data:', error);
        }
    }

    async refreshCalendarView() {
        try {
            // Get current active calendar view
            const views = await this.orm.searchRead('ir.ui.view', [
                ['model', '=', 'calendar.event'],
                ['type', '=', 'calendar']
            ], ['id']);

            if (views && views.length > 0) {
                // Reload calendar view
                await this.action.doAction({
                    type: 'ir.actions.client',
                    tag: 'reload',
                    params: {
                        model: 'calendar.event',
                        view_type: 'calendar'
                    }
                });
            }
        } catch (error) {
            console.error('Error refreshing calendar:', error);
        }
    }

    async addTask() {
        if (!this.state.newTask || !this.state.date) {
            return;
        }

        const taskData = {
            user_id: user.userId,
            date: this.state.date,
            task_title: this.state.newTask,
        };
        try {
            // Create task in personal.organiser
            const taskId = await this.orm.create("personal.organiser", [taskData]);
            // Create event in calendar
            const calendarId = {
                name: this.state.newTask,
                start: this.state.date,
                stop: this.state.date,
                user_id: user.userId,
                allday: true,
            }
            const calendarEventId = await this.orm.create("calendar.event", [calendarId]);
            // Add complete task data to state
            const newTask = {
                id: taskId[0],
                calendar_event_id: calendarEventId[0],
                task_title: this.state.newTask,
                date: this.state.date,
                user_id: user.userId,
            };

            // Add to state and sort
            this.state.tasks.push(newTask);
            this.state.tasks.sort((a, b) => new Date(a.date) - new Date(b.date));

            // Clear input fields
            this.state.newTask = '';
            this.state.date = '';

            // Refresh calendar view
            await this.refreshCalendarView();

        } catch (error) {
            console.error('Error adding task:', error);
        }
    }

    async deleteTask(task) {
        try {
            // Find all related calendar events
            const calendarEvents = await this.orm.searchRead("calendar.event", [
                ["name", "=", task.task_title],
                ["user_id", "=", user.userId]
            ], ['id']);

            // Remove the task from state
            this.state.tasks = this.state.tasks.filter(t => t.id !== task.id);

            // Delete from personal.organiser
            await this.orm.unlink("personal.organiser", [task.id]);

            // Delete all related calendar events
            if (calendarEvents && calendarEvents.length > 0) {
                const calendarEventIds = calendarEvents.map(event => event.id);
                await this.orm.unlink("calendar.event", calendarEventIds);
            }

            // Refresh calendar view
            await this.refreshCalendarView();

        } catch (error) {
            console.error('Error deleting task:', error);
        }
    }

    async onInputChange(event, task, field) {
        const oldValue = task[field];
        const newValue = event.target.value;

        // Validate date if updating date field
        if (field === 'date' && !newValue) {
            return;
        }

        try {
            // First find all existing calendar events with the old title
            const oldCalendarEvents = await this.orm.searchRead("calendar.event", [
                ["name", "=", task.task_title],
                ["user_id", "=", user.userId]
            ], ['id']);

            // Delete old calendar events
            if (oldCalendarEvents && oldCalendarEvents.length > 0) {
                const oldEventIds = oldCalendarEvents.map(event => event.id);
                await this.orm.unlink("calendar.event", oldEventIds);
            }

            // Update personal.organiser
            await this.orm.write("personal.organiser", [task.id], {
                [field]: newValue
            });

            // Create new calendar event
            const calendarEventId = await this.orm.create("calendar.event", [{
                name: field === 'task_title' ? newValue : task.task_title,
                start: field === 'date' ? newValue : task.date,
                stop: field === 'date' ? newValue : task.date,
                start_date: field === 'date' ? newValue : task.date,
                stop_date: field === 'date' ? newValue : task.date,
                user_id: user.userId,
                allday: true,
            }]);

            // Update task in state
            task[field] = newValue;
            task.calendar_event_id = calendarEventId[0];

            // Resort tasks if date was changed
            if (field === 'date') {
                this.state.tasks.sort((a, b) => new Date(a.date) - new Date(b.date));
            }

            // Refresh calendar view
            await this.refreshCalendarView();

        } catch (error) {
            console.error('Error updating task:', error);
            // Revert the state change on error
            task[field] = oldValue;
        }
    }
}