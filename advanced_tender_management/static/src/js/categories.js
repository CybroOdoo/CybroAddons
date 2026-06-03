/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

var CustomForm = publicWidget.Widget.extend({
    selector: '.form-container',
    start: function (ev) {
        var self = this;
        self.$('select.js-example-basic-multiple').select2({
            allowClear: true
        }).on('change', function (e) {
            var selectedValues = $(this).val();
            $('.hidden_categories').remove();
            $('.vendor-registration-form').append(`<input type="hidden" class="hidden_categories" name="many2many_field" value='${JSON.stringify(selectedValues)}'>`);
        });
        }
    });
publicWidget.registry.Many2many_tag = CustomForm;
return CustomForm;