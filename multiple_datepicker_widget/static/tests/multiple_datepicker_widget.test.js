import { expect, test, describe } from "@odoo/hoot";
import { formatLocalDate } from "@multiple_datepicker_widget/js/multiple_date_picker_widget";
import { defineModels, fields, models, mountView } from "@web/../tests/web_test_helpers";

describe("multiple_datepicker_widget", () => {
    describe("formatLocalDate", () => {
        test("preserves local calendar date without UTC timezone shift", () => {
            // A Date object at local midnight Oct 21, 2026
            const localDate = new Date(2026, 9, 21, 0, 0, 0); // Month index 9 is October
            const formatted = formatLocalDate(localDate);

            // Regardless of whether local timezone is UTC+05:30 or UTC+09:00,
            // local format must return the local calendar date '2026-10-21', NOT '2026-10-20'.
            expect(formatted).toBe("2026-10-21");
        });

        test("pads single-digit months and days with leading zeros", () => {
            const jan5 = new Date(2026, 0, 5, 0, 0, 0);
            expect(formatLocalDate(jan5)).toBe("2026-01-05");

            const sep9 = new Date(2026, 8, 9, 0, 0, 0);
            expect(formatLocalDate(sep9)).toBe("2026-09-09");
        });

        test("handles string inputs correctly", () => {
            expect(formatLocalDate("2026-10-21")).toBe("2026-10-21");
            expect(formatLocalDate("  2026-12-31  ")).toBe("2026-12-31");
        });

        test("handles falsy inputs gracefully", () => {
            expect(formatLocalDate(null)).toBe("");
            expect(formatLocalDate(undefined)).toBe("");
            expect(formatLocalDate("")).toBe("");
        });
    });

    describe("DatePickerField component in views", () => {
        class Partner extends models.Model {
            _name = "res.partner";
            name = fields.Char();
            multi_dates = fields.Char();
            _records = [
                { id: 1, name: "Test User", multi_dates: "2026-10-21, 2026-10-22" },
            ];
        }
        defineModels([Partner]);

        test("renders multiple_datepicker widget in edit mode", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 1,
                arch: `
                    <form>
                        <field name="multi_dates" widget="multiple_datepicker"/>
                    </form>
                `,
            });

            expect(".input_datepicker").toHaveCount(1);
            expect(".input_datepicker").toHaveValue("2026-10-21, 2026-10-22");
        });

        test("renders multiple_datepicker widget in readonly mode", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 1,
                arch: `
                    <form>
                        <field name="multi_dates" widget="multiple_datepicker" readonly="1"/>
                    </form>
                `,
            });

            expect(".input_datepicker").toHaveCount(0);
            expect(".o_field_char").toHaveCount(1);
            expect(".o_field_char").toHaveText("2026-10-21, 2026-10-22");
        });
    });
});
