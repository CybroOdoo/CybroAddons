odoo.define('list_tree_pin_records.pin_records', function (require) {
"use strict";

var core = require('web.core');
var ListRenderer = require('web.ListRenderer');
var rpc = require('web.rpc');
var _t = core._t;
var array = [];
var res_id;
/* Add pinning functionality to ListRenderer*/
    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events, {
            "click #pin": 'onClick',
        }),
        /* Add new header to list view */
        _renderHeader: function () {
            var $thead = this._super.apply(this, arguments);
            if (this.hasSelectors) {
            $thead.find('th.o_list_record_selector').before($('<th>', {class: 'o_list_record_selector'}).html('<i class="fa fa-thumb-tack"/>'));
            }
            return $thead;
        },
          /* Get all pinned records */
        _renderBody: function() {
            var self = this;
            var model = this.state.model
            rpc.query({ // rpc query to view pinned records in top of the table.
            model: "pin.record",
            method: "pin_records",
            args: [[model]],
            }).then(function(result) {
            if (result){
                result['id'].forEach(rec => {
                array.push(rec)
                $rows.forEach(element => {
                if (rec == element.res_id) {
                    element.css('background-color', '#ddcef0');
                    element.insertBefore($rows[0]);
                }
                })
                })
            }
            })
            var $rows = this._renderRows();
            return $('<tbody>').append($rows);
        },
          /* Add new pin icon to each row */
        _renderRow: function (record) {
            var $rows = this._super(record);
            var res_id = record.res_id
            $rows.res_id = res_id
            var model = record.model
            if (this.hasSelectors) {
            $rows.find('td.o_list_record_selector').before($('<td>', {class: 'o_list_record_selector'}).html("<i id='pin' value=" + res_id + " model=" + model + " class='fa fa-thumb-tack'/> "));
            }
            return $rows;
        },
          /* Click function of pin icon */
        onClick: function(record) {
            var record_id = record.currentTarget.getAttribute("value")
            var row = $(event.target).parent().parent()[0]
            var model = record.currentTarget.getAttribute("model")
            var num = 0;
            _.each(array, function(line, index) {
            if (line == record_id) {
                row.style.background = 'white',
                array.splice(index, 1)
                num = 1;
            }
            });
            if (num == 0) {
                $($(event.target).parent().parent().parent()[0]).prepend(row)
                array.push(record_id)
                row.style.background = '#ddcef0'
            }
            var self = this;
            rpc.query({ //rpc query to store pinned records in database
            model: "pin.record",
            method: 'save_pin_record',
            args: [
            [parseInt(record_id),model, row.style.background]],
            }).then(function(data) {});
        },
    });
});