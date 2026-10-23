import { describe, expect, test } from "@odoo/hoot";
import {
    contains,
    defineModels,
    fields,
    models,
    mountView,
    mountWithCleanup,
    onRpc,
} from "@web/../tests/web_test_helpers";
import { TimePickerPopover } from "@field_timepicker/js/time_widget";

describe.current.tags("timepicker", "desktop");

class Task extends models.Model {
    _name = "task";

    name = fields.Char({ string: "Task Name" });
    time_char = fields.Char({ string: "Time" });
    time_int = fields.Integer({ string: "Invalid Integer Field" });

    _records = [
        {
            id: 1,
            name: "Initial Task",
            time_char: "10:30:00",
            time_int: 42,
        },
        {
            id: 2,
            name: "Empty Time Task",
            time_char: false,
            time_int: 0,
        },
    ];
}

defineModels([Task]);
onRpc("has_group", () => true);

test("FieldTimePicker renders initial value in form view", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    expect(".o_field_timepicker input").toHaveCount(1);
    expect(".o_field_timepicker input").toHaveValue("10:30:00");
});

test("FieldTimePicker renders empty value when not set", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 2,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    expect(".o_field_timepicker input").toHaveCount(1);
    expect(".o_field_timepicker input").toHaveValue("");
});

test("FieldTimePicker does not open popover when readonly", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker" readonly="1"/>
                </sheet>
            </form>`,
    });

    expect(".o_field_timepicker input").toHaveValue("10:30:00");
    await contains(".o_field_timepicker input").click();
    expect(".time-picker-container").toHaveCount(0);
});

test("FieldTimePicker opens and toggles popover on click", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    expect(".time-picker-container").toHaveCount(0);

    // Click input to open popover
    await contains(".o_field_timepicker input").click();
    expect(".time-picker-container").toHaveCount(1);

    // Clicking input again while open toggles/closes the popover
    await contains(".o_field_timepicker input").click();
    expect(".time-picker-container").toHaveCount(0);
});

test("FieldTimePicker modifies time and updates record on confirm", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    await contains(".o_field_timepicker input").click();
    expect(".time-picker-container").toHaveCount(1);

    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("10");
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("30");
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("00");

    // Increment hour, minute, second
    await contains(".time-box-wrapper:nth-child(1) button:first-of-type").click();
    await contains(".time-box-wrapper:nth-child(2) button:first-of-type").click();
    await contains(".time-box-wrapper:nth-child(3) button:first-of-type").click();

    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("11");
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("31");
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("01");

    // Click 'Set Time'
    await contains(".time-picker-buttons button.btn-primary").click();
    expect(".time-picker-container").toHaveCount(0);
    expect(".o_field_timepicker input").toHaveValue("11:31:01");
});

test("FieldTimePicker cancel button closes popover without updating value", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_char" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    await contains(".o_field_timepicker input").click();
    expect(".time-picker-container").toHaveCount(1);

    // Modify hour
    await contains(".time-box-wrapper:nth-child(1) button:first-of-type").click();
    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("11");

    // Click 'Cancel'
    await contains(".time-picker-buttons button.btn-secondary").click();
    expect(".time-picker-container").toHaveCount(0);
    expect(".o_field_timepicker input").toHaveValue("10:30:00");
});

test("FieldTimePicker shows alert when applied to a non-Char field", async () => {
    await mountView({
        type: "form",
        resModel: "task",
        resId: 1,
        arch: `
            <form>
                <sheet>
                    <field name="time_int" widget="timepicker"/>
                </sheet>
            </form>`,
    });

    await contains(".o_field_timepicker input").click();
    expect(".o_dialog").toHaveCount(1);
    expect(".o_dialog").toHaveText(/This widget can only be added to a 'Char' field\./);
    expect(".time-picker-container").toHaveCount(0);
});

test("TimePickerPopover wrap-around logic for increment and decrement", async () => {
    await mountWithCleanup(TimePickerPopover, {
        props: {
            currentTime: "23:59:00",
            onTimeSelected: (time) => expect.step(`selected: ${time}`),
            close: () => expect.step("closed"),
        },
    });

    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("23");
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("59");
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("00");

    // Hour wraps 23 -> 00
    await contains(".time-box-wrapper:nth-child(1) button:first-of-type").click();
    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("00");

    // Minute wraps 59 -> 00
    await contains(".time-box-wrapper:nth-child(2) button:first-of-type").click();
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("00");

    // Second wraps 00 -> 59
    await contains(".time-box-wrapper:nth-child(3) button:last-of-type").click();
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("59");

    // Click 'Set Time'
    await contains(".time-picker-buttons button.btn-primary").click();
    expect.verifySteps(["selected: 00:00:59", "closed"]);
});

test("TimePickerPopover fallback parsing when currentTime is empty", async () => {
    await mountWithCleanup(TimePickerPopover, {
        props: {
            currentTime: "",
            onTimeSelected: (time) => expect.step(`selected: ${time}`),
            close: () => expect.step("closed"),
        },
    });

    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("00");
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("00");
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("00");

    // Decrement hour 00 -> 23
    await contains(".time-box-wrapper:nth-child(1) button:last-of-type").click();
    expect(".time-box-wrapper:nth-child(1) .time-box-display").toHaveText("23");

    // Decrement minute 00 -> 59
    await contains(".time-box-wrapper:nth-child(2) button:last-of-type").click();
    expect(".time-box-wrapper:nth-child(2) .time-box-display").toHaveText("59");

    // Decrement second 00 -> 59
    await contains(".time-box-wrapper:nth-child(3) button:last-of-type").click();
    expect(".time-box-wrapper:nth-child(3) .time-box-display").toHaveText("59");

    // Click 'Cancel'
    await contains(".time-picker-buttons button.btn-secondary").click();
    expect.verifySteps(["closed"]);
});
