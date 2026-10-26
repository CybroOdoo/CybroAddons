/** @odoo-module **/
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { parseFloatTime } from "@web/views/fields/parsers";
import { useInputField } from "@web/views/fields/input_field_hook";
import { useRecordObserver } from "@web/model/relational_model/utils";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import {
    Component,
    onWillDestroy,
    proxy,
    signal,
    t,
    untrack,
    useOnChange,
    useProps,
} from "@odoo/owl";

// Function for converting the time and return the formatted minutes:seconds.
function formatMinutes(value) {
    if (value === false || value === undefined || value === null || isNaN(value)) {
        return "00:00";
    }
    value = Number(value);
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

function getRecordId(val) {
    if (!val) {
        return false;
    }
    if (Array.isArray(val)) {
        return val[0];
    }
    if (typeof val === "object" && "id" in val) {
        return val.id;
    }
    if (typeof val === "number") {
        return val;
    }
    return false;
}

export class TimerWidget extends Component {
    static template = "automatic_project_task_timer.TimerWidget";
    props = useProps({
        value: t.number().optional(0),
        ongoing: t.boolean().optional(false),
    });

    setup() {
        this.state = proxy({
            duration: this.props.value || 0,
        });
        this.lastDateTime = Date.now();

        useOnChange(
            () => [this.props.ongoing, this.props.value],
            (ongoing, value) => {
                this.state.duration = value || 0;
                if (!ongoing) {
                    this._stopTimers();
                    return;
                }
                this.lastDateTime = Date.now();
                this._runTimer();
                this._runSleepTimer();
                return () => this._stopTimers();
            }
        );

        onWillDestroy(() => this._stopTimers());
    }

    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }

    _stopTimers() {
        clearTimeout(this.tickTimer);
        clearTimeout(this.sleepTimer);
    }

    _runTimer() {
        clearTimeout(this.tickTimer);
        this.tickTimer = setTimeout(() => {
            if (this.props.ongoing) {
                this.state.duration += 1 / 60;
                this._runTimer();
            }
        }, 1000);
    }

    _runSleepTimer() {
        clearTimeout(this.sleepTimer);
        this.sleepTimer = setTimeout(() => {
            if (this.props.ongoing) {
                const diff = Date.now() - this.lastDateTime - 10000;
                if (diff > 1000) {
                    this.state.duration += diff / (1000 * 60);
                }
                this.lastDateTime = Date.now();
                this._runSleepTimer();
            }
        }, 10000);
    }
}

export const taskTimerProps = {
    ...standardFieldProps,
    ongoing: t.boolean().optional(),
    placeholder: t.string().optional(),
};

export class TaskTimer extends Component {
    static template = "TaskTimerTemplate";
    static components = { TimerWidget };
    props = useProps(taskTimerProps);
    numpadDecimalRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        const stageId = getRecordId(this.props.record.data.stage_id);
        const checkStageId = getRecordId(this.props.record.data.check_stage);
        const isTimerStage =
            Boolean(this.props.record.data.task_timer) ||
            Boolean(this.props.record.data.is_user_working) ||
            Boolean(stageId && checkStageId && stageId === checkStageId);

        this.state = proxy({
            duration: isTimerStage ? (this.props.record.data[this.props.name] || 0) : 0,
        });

        useInputField({
            getValue: () => this.durationFormatted,
            ref: this.numpadDecimalRef,
            parse: (v) => parseFloatTime(v),
        });

        useRecordObserver(async (record) => {
            const useSampleModel = untrack(() => record.model?.useSampleModel);
            const currentStageId = getRecordId(record.data.stage_id);
            const currentCheckStageId = getRecordId(record.data.check_stage);
            const currentlyTimerStage =
                Boolean(record.data.task_timer) ||
                Boolean(record.data.is_user_working) ||
                Boolean(currentStageId && currentCheckStageId && currentStageId === currentCheckStageId);

            if (!useSampleModel && currentlyTimerStage && record.resId) {
                const additionalDuration = await this.orm.call(
                    "project.task",
                    "get_working_duration",
                    [record.resId]
                );
                this.state.duration = additionalDuration || 0;
            } else {
                this.state.duration = 0;
            }
        });
    }

    get durationFormatted() {
        return formatMinutes(this.state.duration);
    }

    get ongoing() {
        const stageId = getRecordId(this.props.record.data.stage_id);
        const checkStageId = getRecordId(this.props.record.data.check_stage);
        return Boolean(
            this.props.ongoing !== undefined
                ? this.props.ongoing
                : (this.props.record.data.task_timer ||
                   this.props.record.data.is_user_working ||
                   (stageId && checkStageId && stageId === checkStageId))
        );
    }
}

export const taskTimer = {
    component: TaskTimer,
    displayName: _t("Task Timer"),
    supportedTypes: ["float"],
    extractProps: ({ attrs, placeholder }) => ({
        placeholder,
    }),
};

registry.category("fields").add("task_timer", taskTimer);
registry.category("formatters").add("task_timer", formatMinutes);
