/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";

const { Component, useState, onWillUpdateProps, onWillStart, onWillDestroy } = owl;
// Function for converting the time and return the value in each seconds.
function formatMinutes(value) {
    if (value === false) {
        return "";
    }
    const isNegative = value < 0;
    if (isNegative) {
        value = Math.abs(value);
    }
    let min = Math.floor(value);
    let sec = Math.floor((value % 1) * 60);
    sec = `${sec}`.padStart(2, "0");
    min = `${min}`.padStart(2, "0");
    return `${isNegative ? "-" : ""}${min}:${sec}`;
}

export class TaskTimer extends Component {
//Extend component to add TaskTimer
    setup() {
        this.orm = useService('orm');
        this.state = useState({
            // Duration is expected to be given in minutes
            duration:
                this.props.value !== undefined ? this.props.value : this.props.record.data.duration,
        });
        useInputField({
            getValue: () => this.durationFormatted,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTime(v),
        });

        this.ongoing =
            this.props.ongoing !== undefined
                ? this.props.ongoing
                : this.props.record.data.is_user_working;

        onWillStart(async () => {
        //Check the status while form rendering.
            if(this.props.ongoing === undefined && !this.props.record.model.useSampleModel && this.props.record.data.stage_id[0] == this.props.record.data.check_stage) {
                const additionalDuration = await this.orm.call('project.task', 'get_working_duration', [this.props.record.resId]);
                this.state.duration += additionalDuration;
            }
            if (this.ongoing) {
                this._runTimer();
            }
        });
        onWillUpdateProps((nextProps) => {
            const newOngoing =
                "ongoing" in nextProps
                    ? nextProps.ongoing
                    : "record" in nextProps && nextProps.record.data.is_user_working;
            const rerun = !this.ongoing && newOngoing;
            this.ongoing = newOngoing;
            if (rerun) {
                this.state.duration = nextProps.value;
                this._runTimer();
            }
        });
        onWillDestroy(() => clearTimeout(this.timer));
    }
    //Getting the formatted time duration
    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }
    //Function for setting the interval and call in each 1000ms
    _runTimer() {
        this.timer = setTimeout(() => {
            if (this.ongoing) {
                this.state.duration += 1 / 60;
                this._runTimer();
            }
        }, 1000);
    }
}

TaskTimer.supportedTypes = ["float"];
TaskTimer.template = "TaskTimerTemplate";
//Adding the widget to the field registry
registry.category("fields").add("task_timer", TaskTimer);
registry.category("formatters").add("task_timer", formatMinutes);
