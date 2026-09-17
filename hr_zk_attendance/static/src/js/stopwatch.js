/** @odoo-module **/

import { registry } from "@web/core/registry";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, proxy, signal, onMounted, onWillUnmount } from "@odoo/owl";

// Function to format minutes into HH:MM:SS format
export function formatMinutes(value) {
    if (value === false || value === undefined || value === null) {
        return "";
    }
    const isNegative = value < 0;
    let absVal = Math.abs(value);

    let hours = Math.floor(absVal / 60);
    let minutes = Math.floor(absVal % 60);
    let seconds = Math.floor((absVal % 1) * 60);

    const padSeconds = String(seconds).padStart(2, "0");
    const padMinutes = String(minutes).padStart(2, "0");

    return `${isNegative ? "-" : ""}${hours}:${padMinutes}:${padSeconds}`;
}

export class StopWatch extends Component {
    static template = "StopwatchTemplate";
    static props = {
        ...standardFieldProps,
    };
    input = signal.ref();

    setup() {
        console.group("[StopWatch] setup()");
        console.log("Props:", this.props);

        const initialValue = this.props.record?.data?.[this.props.name] || 0;
        const isLive = Boolean(this.props.record?.data?.is_live_capture);

        this.state = proxy({
            stopwatch: initialValue,
            liveCapture: isLive,
        });

        useInputField({
            ref: this.input,
            getValue: () => this.durationFormatted,
            parse: (v) => parseFloatTime(v),
        });

        onMounted(() => {
            console.log("[StopWatch] Mounted");
            if (this.state.liveCapture) {
                const startTimeStr = this.props.record?.data?.live_capture_start_time;
                if (startTimeStr) {
                    const datetimeObj = new Date(startTimeStr);
                    const now = new Date();
                    const timeDiff = now - datetimeObj;
                    this.state.stopwatch = timeDiff / 1000 / 60;
                    this._runTimer();
                }
            }
        });

        onWillUnmount(() => {
            console.log("[StopWatch] Unmounting, clearing timer");
            if (this.timer) {
                clearTimeout(this.timer);
                this.timer = null;
            }
        });
    }

    get durationFormatted() {
        return formatMinutes(this.state.stopwatch);
    }

    _runTimer() {
        if (!this.state.liveCapture) {
            if (this.timer) {
                clearTimeout(this.timer);
            }
            return;
        }

        this.timer = setTimeout(() => {
            this.state.stopwatch += 1 / 60;
            this._runTimer();
        }, 1000);
    }
}

export const stopWatch = {
    component: StopWatch,
    supportedTypes: ["float"],
};

registry.category("fields").add("stopwatch", stopWatch);
registry.category("formatters").add("stopwatch", formatMinutes);

