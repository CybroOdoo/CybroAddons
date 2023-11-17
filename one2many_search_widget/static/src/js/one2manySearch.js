/** @odoo-module **/
import { registry } from "@web/core/registry";
import { X2ManyField } from "@web/views/fields/x2many/x2many_field";

export class One2ManySearch extends X2ManyField {
    /**
     * Override to include the onInputKeyUp method.
     *
     * Every time entering anything to the text box, the One2many field
     * containing the content of text box will toggle.
     * record and form view.
     *
     */
    onInputKeyUp() {
            var value = $(event.currentTarget).val().toLowerCase();
            var table_id = $(event.currentTarget)[0].id
            $('.o_field_widget.o_field_one2many_search[name="'+ table_id +'"]').find(".o_list_table tr:not(:lt(1))").filter(function() {
                $(this).toggle($(this).text().toLowerCase().indexOf(value) > -1)
            });
        }
}
One2ManySearch.template = "One2ManySearchTemplate";
registry.category("fields").add("one2many_search", One2ManySearch);