odoo.define('listview_change_background_color.colorpicker', function (require) {
"use strict";

var ListRenderer = require('web.ListRenderer');
var dom = require('web.dom');
var rpc = require('web.rpc');

ListRenderer.include({
events: _.extend({}, ListRenderer.prototype.events, {
    'click .color_picker': 'click_colorpicker',
    'change .color_picker': 'click_colorpicker',
}),
/**
 * The _renderView function for calling the get_color()
 * @override
 */
_renderView: function () {
        var self = this;
        return this._super.apply(this, arguments).then(function () {
            self.get_color();
        });
    },
/**
 * When click the color label the selected color is passing to
 * the color.picker model with current model and res_id
 */
click_colorpicker: function(ev) {
    let res_id = ev.target.dataset.id;
    ev.stopPropagation();
    var color = ev.target.value
    var res_model = this.state.model;
    rpc.query({
        model: 'color.picker',
        method: 'get_color_picker_model_and_id',
        kwargs: {
            record: res_id,
            model_name: res_model,
            record_color: color,
        },
    });
    ev.target.parentNode.parentNode.style.backgroundColor = color
},
/**
 * Rendering checkbox having input type color
 */
_renderSelectorColor: function(tag, record) {
    dom.renderCheckbox().find("input[type='checkbox']").prop('disabled');
    return $('<' + tag + '>')
        .append($('<input type="color" class="color_picker" data-id="' + record.res_id + '" value="#e7d8d5" style="width:20px;border: 1px;height: 20px;"/>'));
},
/**
 * Override _renderHeader to add color heading.
 * @override
 */
_renderHeader: function() {
    var $thead = this._super.apply(this, arguments);
    if (this.hasSelectors) {
        $thead.find('th.o_list_record_selector').after($('<th>', {
            class: 'o_list_serial_number_header'
        }).html('Color'));
    }
    return $thead;
},
/**
 * Override _renderRow to add color in dataset.
 * @override
 */
_renderRow: function(record) {
    const $tr = this._super(...arguments);
    if (this.hasSelectors) {
        $tr.find('.o_list_record_selector').after(this._renderSelectorColor('td', record));
    }
    return $tr;
},
/**
 * The function will search the coloured rows and the color is set to the background color of rows
 */
get_color: function() {
    var current_model = this.state.model;
    this.$el.find('.o_data_row').ready(() => {
        let tr_list = this.$el.find('.o_data_row')
        rpc.query({
            model: 'color.picker',
            method: 'search_read',
            domain: [
                ['res_model', '=', current_model]
            ],
        }).then(function(data) {
            Array.prototype.forEach.call(tr_list, function(tr) {
                data.forEach((item) => {
                    if (tr.firstChild.nextElementSibling.firstChild.dataset.id == item.record) {
                        tr.style.backgroundColor = item.color
                    }
                });
            });
        });
    })
},
});
});
