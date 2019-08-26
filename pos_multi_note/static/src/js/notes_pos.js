odoo.define('pos_multi_note.notes_pos', function (require) {
    "use strict";
    var screens = require('point_of_sale.screens');
    var gui = require('point_of_sale.gui');
    var core = require('web.core');
    var rpc = require('web.rpc');
    var PopupWidget = require('point_of_sale.popups');
    var _t = core._t;
    var models = require('point_of_sale.models');

    models.load_models({
        model: 'pos.order.note',
        fields: ['pos_note'],
        loaded: function (self, ordernotes) {
            self.order_note_by_id = {};
            for (var i = 0; i < ordernotes.length; i++) {
                self.order_note_by_id[ordernotes[i].id] = ordernotes[i];
            }
        }
    });

    var NotePopupWidget = PopupWidget.extend({
        count: 0,
        template: 'NotePopupWidget',
        events: _.extend({}, PopupWidget.prototype.events, {
            'change .note_temp': 'click_option'
        }),
        init: function (parent, options) {
            this.options = options || {};
            this._super(parent, _.extend({}, {
                size: "medium"
            }, this.options));
        },
        renderElement: function () {
            this._super();
            for (var note in this.pos.order_note_by_id) {
                $('#note_select').append($("<option>" + this.pos.order_note_by_id[note].pos_note + "</option>").attr("value", this.pos.order_note_by_id[note].pos_note)
                    .attr("id", this.pos.order_note_by_id[note].id)
                    .attr("class", "note_option"))
            }
        },
        show: function (options) {
            options = options || {};
            this._super(options);
            $('textarea').text(options.value);
        },
        click_confirm: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var line = this.pos.get_order().get_selected_orderline();
            line.set_note($('#note_text_area').val());
            this.gui.close_popup();
        },
        click_option: function (event) {
            event.preventDefault();
            event.stopPropagation();
            var old_text = $('textarea').val();
            var e = document.getElementById("note_select");
            var text = e.options[e.selectedIndex].value;
            old_text += "\n";
            old_text += text;
            $('textarea').text(old_text);
        }

    });
    gui.define_popup({name: 'pos_no', widget: NotePopupWidget});

    var InternalNoteButton = screens.ActionButtonWidget.extend({
        template: 'InternalNoteButton',
        button_click: function () {
            var line = this.pos.get_order().get_selected_orderline();
            if (line) {
                this.gui.show_popup('pos_no', {
                    value: line.get_note(),
                    'title': _t('ADD YOUR MULTIPLE ORDER NOTES')
                });
            }
        }
    });

    screens.define_action_button({
        'name': 'pos_internal_note',
        'widget': InternalNoteButton,
        'condition': function () {
            return this.pos.config.note_config;
        }
    });
});

