/** @odoo-module **/
import { _t } from 'web.core';
import { useService } from "@web/core/utils/hooks";
import { Many2ManyTagsFieldColorEditable } from "@web/views/fields/many2many_tags/many2many_tags_field";
import { patch } from "@web/core/utils/patch";
const Dialog = require('web.Dialog');

patch(Many2ManyTagsFieldColorEditable.prototype, '/advanced_many2many_tags/static/src/js/many2many_tags_field.js', {
    /*Here Many2ManyTagsFieldColorEditable is patched to over ride onBadgeClick()*/
    setup() {
        this._super.apply(this, arguments);
        this.notification = useService("notification");
        this.action = useService("action");
    },
    onBadgeClick(ev, record) {
        /*This function is override to open a dialog box on click of
        many2many field and the value is copied if copy button is clicked .
        If open form view is clicked then form view of the field is opened.*/
        var copytext = ev.target.innerText;
        var buttons = [
            {
                text: _t("Ok"),
                classes: 'btn-primary',
                close: true,
            },
        ];
        new Dialog(self, {
            size: 'medium',
            buttons: [
                {
                    text: _t("Copy Text"), classes: 'btn-primary', close: true,
                    click: () => {
                        navigator.clipboard.writeText(copytext);
                        this.notification.add(
                            this.env._t("Copied the text: " + copytext),
                            {
                                title: this.env._t("Success"),
                                type: "success",
                            },
                        );
                    },
                },
                {
                    text: _t("Open Form View"), classes: 'btn-primary', close: true,
                    click: () => {
                        this.action.doAction({
                            type: 'ir.actions.act_window',
                            res_model: this.props.relation,
                            res_id: record.data.id,
                            views: [[false, 'form']],
                            target: 'current',
                        });
                    },
                },
                {
                    text: _t("Cancel"), close: true
                },
            ],
            $content: $('<div>', {
                text: _t(" If you want to copy text click 'Copy Text'. If you want to open form view click 'Open Form View'. "),
            }),
        }).open();
        return this._super.apply(this, arguments);
    }
})