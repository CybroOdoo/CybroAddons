import { describe, expect, test } from "@odoo/hoot";
import { defineModels, fields, models, mountView } from "@web/../tests/web_test_helpers";
import { JsonWidget } from "@advanced_json_widget/components/json_widget/json_widget";

describe.current.tags("desktop");

describe("advanced_json_widget", () => {
    describe("formatJsonToEntries", () => {
        test("converts JS object to key-value entries", () => {
            const entries = JsonWidget.prototype.formatJsonToEntries({ name: "Odoo", version: 20 });
            expect(entries.length).toBe(2);
            expect(entries[0].key).toBe("name");
            expect(entries[0].value).toBe("Odoo");
            expect(entries[1].key).toBe("version");
            expect(entries[1].value).toBe("20");
        });

        test("parses JSON string into entries", () => {
            const entries = JsonWidget.prototype.formatJsonToEntries('{"role": "developer"}');
            expect(entries.length).toBe(1);
            expect(entries[0].key).toBe("role");
            expect(entries[0].value).toBe("developer");
        });

        test("handles invalid JSON string gracefully", () => {
            const entries = JsonWidget.prototype.formatJsonToEntries("not a json");
            expect(entries).toEqual([]);
        });

        test("handles null or non-object values gracefully", () => {
            expect(JsonWidget.prototype.formatJsonToEntries(null)).toEqual([]);
            expect(JsonWidget.prototype.formatJsonToEntries(undefined)).toEqual([]);
            expect(JsonWidget.prototype.formatJsonToEntries(123)).toEqual([]);
        });

        test("stringifies nested objects and arrays", () => {
            const entries = JsonWidget.prototype.formatJsonToEntries({
                config: { theme: "dark" },
                tags: ["erp", "web"],
            });
            expect(entries[0].value).toBe('{"theme":"dark"}');
            expect(entries[1].value).toBe('["erp","web"]');
        });
    });

    describe("formatEntriesToJson", () => {
        test("converts entries array back into JSON object", () => {
            const context = {
                state: {
                    entries: [
                        { key: "company", value: "Cybrosys" },
                        { key: "location", value: "India" },
                    ],
                },
            };
            const result = JsonWidget.prototype.formatEntriesToJson.call(context);
            expect(result).toEqual({ company: "Cybrosys", location: "India" });
        });

        test("filters out empty keys", () => {
            const context = {
                state: {
                    entries: [
                        { key: "", value: "val1" },
                        { key: "   ", value: "val2" },
                        { key: "valid", value: "ok" },
                    ],
                },
            };
            const result = JsonWidget.prototype.formatEntriesToJson.call(context);
            expect(result).toEqual({ valid: "ok" });
        });

        test("parses booleans, null, numbers, and JSON types", () => {
            const context = {
                state: {
                    entries: [
                        { key: "is_active", value: "true" },
                        { key: "is_deleted", value: "false" },
                        { key: "empty_val", value: "null" },
                        { key: "count", value: "42" },
                        { key: "price", value: "19.99" },
                        { key: "items", value: "[1, 2]" },
                    ],
                },
            };
            const result = JsonWidget.prototype.formatEntriesToJson.call(context);
            expect(result.is_active).toBe(true);
            expect(result.is_deleted).toBe(false);
            expect(result.empty_val).toBe(null);
            expect(result.count).toBe(42);
            expect(result.price).toBe(19.99);
            expect(result.items).toEqual([1, 2]);
        });

        test("trims whitespace from keys and values", () => {
            const context = {
                state: {
                    entries: [{ key: "  user  ", value: "  alice  " }],
                },
            };
            const result = JsonWidget.prototype.formatEntriesToJson.call(context);
            expect(result).toEqual({ user: "alice" });
        });
    });

    describe("JsonWidget component in views", () => {
        class ResPartner extends models.Model {
            _name = "res.partner";

            name = fields.Char({ string: "Name" });
            json_data = fields.Json({ string: "JSON Field" });
            char_data = fields.Char({ string: "Char Field" });

            _records = [
                {
                    id: 1,
                    name: "Partner 1",
                    json_data: { role: "admin", active: true, count: 5 },
                    char_data: JSON.stringify({ theme: "dark", level: 1 }),
                },
                {
                    id: 2,
                    name: "Partner 2 (Empty)",
                    json_data: null,
                    char_data: "",
                },
            ];
        }

        defineModels([ResPartner]);

        test("renders JSON widget tags when field has data", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 1,
                arch: `
                    <form>
                        <field name="json_data" widget="json_widget"/>
                    </form>
                `,
            });

            expect(".o_field_json").toHaveCount(1);
            expect(".o_field_json").toHaveClass("o_tags_input");
            expect(".o_field_json").toHaveClass("o_input");
            expect(".o_field_json .badge").toHaveCount(3);
            expect(".o_field_json .badge:eq(0)").toHaveText("role");
            expect(".o_field_json .badge:eq(1)").toHaveText("active");
            expect(".o_field_json .badge:eq(2)").toHaveText("count");
            expect(".o_field_json .text-muted:contains(Click to add data)").toHaveCount(0);
        });

        test("renders placeholder 'Click to add data' when field is empty", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 2,
                arch: `
                    <form>
                        <field name="json_data" widget="json_widget"/>
                    </form>
                `,
            });

            expect(".o_field_json").toHaveCount(1);
            expect(".o_field_json .badge").toHaveCount(0);
            expect(".o_field_json .text-muted:contains(Click to add data)").toHaveCount(1);
        });

        test("renders readonly mode without input edit styling", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 1,
                arch: `
                    <form>
                        <field name="json_data" widget="json_widget" readonly="1"/>
                    </form>
                `,
            });

            expect(".o_field_json").toHaveCount(1);
            expect(".o_field_json").not.toHaveClass("o_tags_input");
            expect(".o_field_json").not.toHaveClass("o_input");
            expect(".o_field_json .badge").toHaveCount(3);
        });

        test("renders correctly with Char field containing JSON string", async () => {
            await mountView({
                type: "form",
                resModel: "res.partner",
                resId: 1,
                arch: `
                    <form>
                        <field name="char_data" widget="json_widget"/>
                    </form>
                `,
            });

            expect(".o_field_json").toHaveCount(1);
            expect(".o_field_json .badge").toHaveCount(2);
            expect(".o_field_json .badge:eq(0)").toHaveText("theme");
            expect(".o_field_json .badge:eq(1)").toHaveText("level");
        });
    });
});
