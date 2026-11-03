/** @odoo-module **/
import { Component, proxy } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";

export class PersonalOrganizer extends Component {
    static template = 'personal_organiser.task';

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
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
        try {
            // The task creates its own all-day calendar event on the server.
            const [taskId] = await this.orm.create("personal.organiser", [{
                user_id: user.userId,
                date: this.state.date,
                task_title: this.state.newTask,
            }]);
            this.state.tasks.push({
                id: taskId,
                task_title: this.state.newTask,
                date: this.state.date,
            });
            this.state.tasks.sort((a, b) => new Date(a.date) - new Date(b.date));
            this.state.newTask = '';
            this.state.date = '';
            await this.refreshCalendarView();
        } catch (error) {
            console.error('Error adding task:', error);
        }
    }

    async deleteTask(task) {
        try {
            // Deleting the task also deletes its own calendar event.
            await this.orm.unlink("personal.organiser", [task.id]);
            this.state.tasks = this.state.tasks.filter(t => t.id !== task.id);
            await this.refreshCalendarView();
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    }

    async onInputChange(event, task, field) {
        const oldValue = task[field];
        const newValue = event.target.value;
        if (field === 'date' && !newValue) {
            return;
        }
        try {
            // The server moves or renames the task's calendar event.
            await this.orm.write("personal.organiser", [task.id], {
                [field]: newValue
            });
            task[field] = newValue;
            if (field === 'date') {
                this.state.tasks.sort((a, b) => new Date(a.date) - new Date(b.date));
            }
            await this.refreshCalendarView();
        } catch (error) {
            console.error('Error updating task:', error);
            task[field] = oldValue;
        }
    }
}
