/** @odoo-module **/
import { registry } from "@web/core/registry";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class One2ManySearch extends X2ManyField {
//  Whenever text is entered into the search input box, it dynamically
//  filters the content of the One2Many field to display only matching records
   onInputKeyUp(event) {
    const value = event.currentTarget.value.toLowerCase();
    const rows = document.querySelectorAll(".o_list_table tbody tr");
    rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(value) ? "" : "none";
    });
}
}
One2ManySearch.template = "One2ManySearchTemplate";
export const one2ManySearch = {
    ...x2ManyField,
    component: One2ManySearch,
};
registry.category("fields").add("one2many_search", one2ManySearch);
