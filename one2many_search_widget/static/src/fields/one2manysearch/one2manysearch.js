/** @odoo-module **/
import { registry } from "@web/core/registry";
import { X2ManyField, x2ManyField } from "@web/views/fields/x2many/x2many_field";

export class One2ManySearch extends X2ManyField {
//  Override to include the onInputKeyUp method.
//  Whenever text is entered into the search input box, it dynamically
//  filters the content of the One2Many field to display only matching records
    onInputKeyUp() {
        var value = $(event.currentTarget).val().toLowerCase();
        $(".o_list_table tr:not(:lt(1))").filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
        });
    }
}
One2ManySearch.template = "One2ManySearchTemplate";
export const one2ManySearch = {
    ...x2ManyField,
    component: One2ManySearch,
};
registry.category("fields").add("one2many_search", one2ManySearch);
