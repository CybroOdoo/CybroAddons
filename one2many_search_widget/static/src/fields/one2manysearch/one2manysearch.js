/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useSubEnv } from "@web/owl2/utils";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

// Dynamically resolve parent field definition (sol_o2m -> section_and_note_one2many -> x2ManyField)
const baseFieldDef = registry.category("fields").get("sol_o2m", null)
    || registry.category("fields").get("section_and_note_one2many", null)
    || x2ManyField;

const BaseComponent = baseFieldDef.component || X2ManyField;

export class One2ManySearch extends BaseComponent {
    setup() {
        super.setup();
        if (!this.env.shouldCollapse) {
            useSubEnv({
                shouldCollapse: (record, fieldName) => false,
            });
        }
    }

    // Whenever text is entered into the search input box, it dynamically
    // filters the content of the One2Many field to display only matching records
    onInputKeyUp(event) {
        const value = event.currentTarget.value.toLowerCase();
        const container = event.currentTarget.closest(".o_field_x2many") || document;
        const rows = container.querySelectorAll(".o_list_table tbody tr");
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(value) ? "" : "none";
        });
    }
}

One2ManySearch.template = "One2ManySearchTemplate";

export const one2ManySearch = {
    ...baseFieldDef,
    component: One2ManySearch,
    additionalClasses: [...(baseFieldDef.additionalClasses || []), ...(x2ManyField.additionalClasses || [])],
};

registry.category("fields").add("one2many_search", one2ManySearch);
