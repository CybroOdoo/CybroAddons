/** @odoo-module **/
import { registry } from '@web/core/registry';
import { parseFloatTime } from '@web/views/fields/parsers';
import { useInputField } from '@web/views/fields/input_field_hook';
import { Component, useState, onMounted } from '@odoo/owl';

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
export class StopWatch extends Component {
    static template = "StopwatchTemplate";
    setup() {
        this.state = useState({
            stopwatch: 0,
            livecapture: this.props.record.data.is_live_capture
        });

        useInputField({
            getValue: () => this.durationFormatted,
            refName: "numpadDecimal",
            parse: (v) => parseFloatTime(v),
        });

        onMounted(async () => {
            if (this.state.livecapture) {
                const datetimeObj = new Date(this.props.record.data.live_capture_start_time);
                const now = new Date();
                const timeDiff = now - datetimeObj;
                this.state.stopwatch = timeDiff / 1000 / 60;
                this._runTimer();
            }
        });
    }
    get durationFormatted() {
        return formatMinutes(this.state.stopwatch);
    }
    _runTimer() {
        if (!this.state.livecapture) {
            clearTimeout(this.timer);
            return;
        }
        this.timer = setTimeout(async () => {
            this.state.stopwatch += 1 / 60;
            this._runTimer();
        }, 1000);
    }
}
registry.category("fields").add("stopwatch", StopWatch);
registry.category("formatters").add("stopwatch", formatMinutes);
