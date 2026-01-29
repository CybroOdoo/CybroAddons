/** @odoo-module **/
import { registry } from "@web/core/registry";
const { Component,  useState } = owl;
const { useRef } = owl.hooks;
import { Dropdown } from "@web/core/dropdown/dropdown";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
/** @extends Component to add methods of timesheet view */
export class TimesheetSystray extends Component {
    async setup() {
        this.orm = useService("orm");
        this.notification = useService("notification")
        this.timesheet = useRef("Timesheet")
        this.state = useState({
            project: [],
            task: [],
            start: false,
            WorkTime: null,
            timer: false,
            Project: 0,
            Task: 0,
            time: '',
            paused: null,
            pausedTime: null,
            distance: null,
            current_task: [],
            Access: null
        })
        if ((await this.env.services.user.hasGroup('project.group_project_user') || await this.env.services.user.hasGroup('project.group_project_manager')) && (await this.env.services.user.hasGroup('hr_timesheet.group_hr_timesheet_approver') || await this.env.services.user.hasGroup('hr_timesheet.group_hr_timesheet_user') || await this.env.services.user.hasGroup('hr_timesheet.module_category_services_timesheets'))) {
            this.state.Access = true
            this.SearchReadTimeSheet()
            this.state.project = await this.orm.searchRead('project.project', [])
            this.state.Task = await this.orm.searchRead('project.task', [])
        } else {
            this.state.Access = false
        }
    }
    currentDT() {
        const currentDT = new Date();
        const year = currentDT.getFullYear().toString().padStart(4, '0');
        const month = String(currentDT.getMonth() + 1).padStart(2, '0'); //Months are zero-indexed. so,add 1
        const day = currentDT.getDate().toString().padStart(2, '0');
        const hours = currentDT.getHours().toString().padStart(2, '0');
        const minutes = currentDT.getMinutes().toString().padStart(2, '0');
        const seconds = currentDT.getSeconds().toString().padStart(2, '0');
        return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`;
    }
    async SearchReadTimeSheet() {
        this.employee = await this.orm.searchRead('hr.employee',
            [
                ["user_id", "=", this.env.services.user.userId]
            ])
        this.state.current_task = await this.orm.searchRead('account.analytic.line',
            [
                ["employee_id", "=", this.employee[0].id],
                ['is_current', '=', true]
            ])
        if (this.state.current_task[0]) {
            if (this.state.current_task[0]['end_time']) {
                if (this.state.current_task[0]['current_state'] == 'pause') {
                    var datetime = new Date(new Date().getTime())
                    this.state.time = this.state.current_task[0]['pausing_time']
                    this.state.paused = true;
                    this.state.WorkTime = true
                } else {
                    this.state.WorkTime = true
                    this.state.time = this.state.current_task[0]['pausing_time']
                    const newDate = new Date()
                    const timeParts = this.state.time.split(/[hms\s]+/);
                    this.state.paused = false;
                    newDate.setHours(newDate.getHours() - parseInt(timeParts[0]));
                    newDate.setMinutes(newDate.getMinutes() - parseInt(timeParts[1]));
                    newDate.setSeconds(newDate.getSeconds() - parseInt(timeParts[2]));
                    this.StartCountTime(new Date(newDate).getTime())
                }
            } else {
                this.current_time = new Date(this.state.current_task[0]['start_time'])
                this.state.WorkTime = true
                this.StartCountTime(this.current_time.getTime())
            }
        } else {
            return
        }
    }
    /** Start counting the time **/
    async StartTime() {
        this.SearchReadTimeSheet()
        this.MainDiv = this.timesheet.el
        if (!this.MainDiv.querySelector(".Project").value ||
            !this.MainDiv.querySelector(".Task").value) {
            return this.notification.add(_t("Choose Project and Task"), {
                type: 'warning'
            })
        }
        this.state.start = true;
        this.state.WorkTime = true;
        this.state.time = this.MainDiv.querySelector(".time").innerHTML;
        this.state.Project = this.MainDiv.querySelector(".Project").value
        this.state.Task = this.MainDiv.querySelector(".Task").value
        this.state.timer = new Date().getTime()
        await this.orm.create("account.analytic.line", {
            project_id: parseInt(this.state.Project),
            task_id: parseInt(this.state.Task),
            start_time: await this.currentDT(),
            name: " ",
            is_current: true
        });
        this.SearchReadTimeSheet()
    }
    /** Pause the time and store the time **/
    async PauseTime() {
        await this.orm.write("account.analytic.line", [this.state.current_task[0].id], {
            end_time: await this.currentDT(),
            pausing_time: this.state.time,
            current_state: 'pause'
        })
        await clearInterval(this.StopWatch);
        this.state.paused = true;
        window.location.reload();
    }
    /** Start after pause and change the state **/
    async PlayTime() {
        this.state.pausedTime = this.state.current_task[0].pausing_time
        await this.orm.write("account.analytic.line", [this.state.current_task[0].id], {
            current_state: 'play'
        })
        this.SearchReadTimeSheet()
    }
    /** Add timesheet based on project, task and time **/
    async AddTimesheet() {
        if (!this.timesheet.el.querySelector(".Description").value) {
	        return this.notification.add(_t("Add a Description"), { type: 'warning'});
	    }else {
	        /** Convert 02h 30m format time => 02:30 and create timesheet**/
	        const timeParts =  this.state.time.split(/h |m/);
            const hours = Number(timeParts[0]);
            const minutes = Number(timeParts[1]);
            await this.orm.write("account.analytic.line", [this.state.current_task[0].id], {
                end_time: await this.currentDT(),
                unit_amount: hours + minutes / 60,
			    name: this.timesheet.el.querySelector(".Description").value,
                is_current : false
            })
        }
        await clearInterval(this.StopWatch);
		this.state.time = ''
		this.state.WorkTime = false;
		window.location.reload()
	}
    /** Running the count down using setInterval function */
    StartCountTime(start_time) {
        var self = this
        self.StopWatch = setInterval(function() {
            var currentTime = new Date().getTime()
            self.state.distance = currentTime - start_time
            var days = Math.floor(self.state.distance / (1000 * 60 * 60 * 24));
            var hours = Math.floor((self.state.distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            var minutes = Math.floor((self.state.distance % (1000 * 60 * 60)) / (1000 * 60));
            var seconds = Math.floor((self.state.distance % (1000 * 60)) / 1000);
            if (hours && minutes && seconds) {
                self.state.time = hours + "h " + minutes + "m " + seconds + 's';
            } else if (minutes && seconds) {
                self.state.time = "00h " + minutes + "m " + seconds + 's';
            } else if (seconds) {
                self.state.time = '00h 00m ' + seconds + 's';
            } else {
                self.state.time = '00h 00m 00s';
            }
            self.orm.write("account.analytic.line", [self.state.current_task[0].id], {
                pausing_time: self.state.time
            })
        }, 1000);
    }
    /** Filter the tasks bases on selected project **/
    async ChangeProject(project_id) {
        if (project_id) {
            this.state.Task = await this.orm.searchRead('project.task',
                [
                    ["project_id", "=", parseInt(project_id)]
                ])
        }
    }
    /** Filter the tasks bases on selected project **/
    async ChangeTask(task_id) {
        if (task_id) {
            var project = await this.orm.searchRead('project.project', [
                ["task_ids", "in", [parseInt(task_id)]]
            ])
            this.timesheet.el.querySelector(".Project").value = project[0].id
        }
    }
}
TimesheetSystray.template = "TimesheetSystray";
TimesheetSystray.components = {
    Dropdown
};
export const systrayItem = {
    Component: TimesheetSystray,
};
registry.category("systray").add("TimesheetSystray", systrayItem, {
    sequence: 105
});
