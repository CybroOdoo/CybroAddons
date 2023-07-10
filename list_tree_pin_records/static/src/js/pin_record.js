/** @odoo-module **/

import core from 'web.core';
import ListRenderer from 'web.ListRenderer';
import rpc from 'web.rpc';
var _t = core._t;
var array = [];
var res_id;
/* Add pin icon in list view*/
    ListRenderer.include({
        events: _.extend({}, ListRenderer.prototype.events,{
        "click #pin": '_onClick',
        }),
        //   Add new header
        _renderHeader: function() {
            var $thead = this._super.apply(this, arguments);
            if (this.hasSelectors) {
            $thead.find('th.o_list_record_selector').before($('<th>', {class: 'o_list_record_selector'}).html('<i class="fa fa-thumb-tack"/>'));
            }
            return $thead;
        },
        //  Get all pinned records when refreshing page
        _renderBody: function() {
            var self = this;
            var $rows = this._renderRows();
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
            return $('<tbody>').append($rows);
        },
        //      Add pin icon in each row
        _renderRow: function(record, index) {
            var $rows = this._super.apply(this, arguments);
            var res_id = record.res_id
            $rows.res_id = res_id
            var model = record.model
            if (this.hasSelectors) {
                res_id = record.res_id
                $rows.find('td.o_list_record_selector').before($('<td>', {class: 'o_list_record_selector'}).html("<i id='pin' value=" + res_id + " model=" + model + " class='fa fa-thumb-tack'/> "));
                }
            return $rows;
        },
        //   click function of pin icon
        _onClick: function(record) {
            var record_id = record.currentTarget.getAttribute("value")
            var row = $(event.target).parent().parent()[0]
            var model = record.currentTarget.getAttribute("model")
            var index =array.indexOf(parseInt(record_id));
            if (index != -1){
                row.style.background='white',
                delete array[index]
            }
            else {
                $($(event.target).parent().parent().parent()[0]).prepend(row)
                array.push(parseInt(record_id))
                row.style.background = '#ddcef0'
            }
            var self = this;
            rpc.query({ //rpc query to store pinned records in database
            model: 'pin.record',
            method: 'save_pin_record',
            args: [[parseInt(record_id),model, row.style.background]],
            }).then(function(data) {});
        }
    });