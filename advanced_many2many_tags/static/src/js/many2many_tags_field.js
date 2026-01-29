/** @odoo-module **/
var core = require('web.core');
import relational_fields from 'web.relational_fields';
const Dialog = require('web.Dialog');

var M2MTags = relational_fields.FormFieldMany2ManyTags;
var _t = core._t;
var FieldMany2ManyTagsOpen = M2MTags.include({
    /* Here a new click function is added to the many2many_tags. */
    events: _.extend({}, M2MTags.prototype.events, {
        'click .badge': '_onOpenTag'
    }),
    init: function () {
        this._super.apply(this, arguments);
    },
    _onOpenTag: function (ev) {
        /*
        This function is used to open a dialog box on clicking the
        Many2many field with many2many_tags widget and the value is copied if
        copy button is clicked. If clicked on the open form view button, then
        form view of the record is opened.
        */
        ev.preventDefault();
        var copytext = ev.target.innerText;
        new Dialog(self, {
            size: 'medium',
            buttons: [
                {
                    text: _t("Copy Text"), classes: 'btn-primary', close: true,
                    click: () => {
                        navigator.clipboard.writeText(copytext);
                        this.displayNotification({ title: _t("Success"),
                        message: _t("Copied the text: " + copytext), type: 'success' });
                    }
                },
                {
                    text: _t("Open Form View"), classes: 'btn-primary', close: true,
                    click: () => {
                        this.do_action({
                            type: 'ir.actions.act_window',
                            res_model: this.field.relation,
                            res_id: this.value.data[0].data.id,
                            views: [[false, 'form']],
                            target: 'current'
                        });
                    }
                },
                {
                    text: _t("Cancel"), close: true
                }
            ],
            $content: $('<div>', {
                text: _t(" If you want to copy text click 'Copy Text'. If you want to open form view click 'Open Form View'. "),
            })
        }).open();
    }
});
return {
    FieldMany2ManyTagsOpen: FieldMany2ManyTagsOpen
};