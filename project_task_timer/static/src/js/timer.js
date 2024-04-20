/** @odoo-module **/
// Import statements for necessary modules and utilities
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, onWillStart, useState, onWillUpdateProps, onWillDestroy, useRef, onMounted } from "@odoo/owl";
// Function to format minutes into HH:MM:SS format
function formatMinutes(value) {
    if (value === false) {
        return "";
    }
    const isNegative = value < 0;
    if (isNegative) {
        value = Math.abs(value);
    }
    let hours = Math.floor(value / 60);
    let minutes = Math.floor(value % 60);
    let seconds = Math.floor((value % 1) * 60);
    seconds = `${seconds}`.padStart(2, "0");
    minutes = `${minutes}`.padStart(2, "0");
    return `${isNegative ? "-" : ""}${hours}:${minutes}:${seconds}`;
}
export class TaskTimer extends Component {
    static template = "TaskTimerTemplate";
    static props = {
        ...standardFieldProps
    };
    setup() {
        this.orm = useService('orm');
        this.toggle = useRef("toggleButton");
        this.timerRunning = false;
        this.state = useState({
            duration: this.props.value !== undefined ? this.props.value : this.props.record.data.duration,
        });
        // Hook to handle input field related operations
        useInputField({
            getValue: () => this.durationFormatted,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTime(v),
        });
        // Functions triggered after the component is mounted
        onMounted(() => {
            if (this.props.record.data.task_timer) {
                this.toggle.el.checked = true;
                this._runTimer();
                this.timerRunning = true;
            }
        });
        // Functions triggered before the component starts
        onWillStart(async () => {
            // Update duration if ongoing and task timer is active
            if (this.props.ongoing === undefined && !this.props.record.model.useSampleModel && this.props.record.data.task_timer) {
                const additionalDuration = await this.orm.call('project.task', 'get_working_duration', [this.props.record.resId]);
                this.state.duration += additionalDuration;
            }
            // Start the timer if ongoing and task timer is active
            if (this.props.ongoing) {
                if (this.props.record.data.task_timer) {
                    this._runTimer();
                }
            }
        });
        // Functions triggered before the component is destroyed
        onWillDestroy(() => clearTimeout(this.timer));
    }
    // Computed property to get the formatted duration
    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }
    // Toggle function to start/stop the timer
    async toggleFunction() {
        if (this.timerRunning) {
            // Stop the timer
            clearTimeout(this.timer);
            this.timerRunning = false;
            await this.orm.call('project.task', 'action_toggle_start', [this.props.record.resId, this.timerRunning]);
            window.location.reload(); // Reload the window
        } else {
            // Start the timer
            this._runTimer();
            this.timerRunning = true;
            await this.orm.call('project.task', 'action_toggle_start', [this.props.record.resId, this.timerRunning]);
        }
    }
    // Function to run the timer
    _runTimer() {
        this.timer = setTimeout(() => {
            // Increment the duration every second
            this.state.duration += 1 / 60;
            this._runTimer(); // Call recursively to create a continuous timer effect
        }, 1000);
    }
}
// Definition of taskTimer as a component
export const taskTimer = {
    component: TaskTimer,
    supportedTypes: ["float"],
};
// Register the taskTimer component under the "fields" category
registry.category("fields").add("task_timer", taskTimer);

// Register the formatMinutes function under the "formatters" category
registry.category("formatters").add("task_timer", formatMinutes);
