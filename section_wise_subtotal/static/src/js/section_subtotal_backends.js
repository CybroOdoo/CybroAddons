/** @odoo-module
 * This module help us to calculate the section wise subtotal in
 * Sale order and Purchase order.
 **/
 odoo.define('section_wise_subtotal.section_subtotal_backends', function(require){
"use strict";

var basic_fields = require('web.basic_fields');
var SectionAndNoteListRenderer = require('account.section_and_note_backend');

SectionAndNoteListRenderer.include({
/**
     * We want section and note to take the whole line (except handle and trash)
     * to look better and to hide the unnecessary fields.
     *
     * @override
     */
    _renderBodyCell: function (record, node, index, options) {
    /** The function that hide all the fields except subtotal field in section.**/
        var $cell =this._super.apply(this, arguments);

        var section = record.data.display_type === 'line_section';
        if (section && this.arch.attrs['section_wise_subtotal']){
            var sectionSubtotal = this.arch.attrs['section_wise_subtotal'].split(',');
            if (node.attrs.name ==="name"){
                var nbrColumns = this._getNumberOfCols();
                if (this.handleField){
                    nbrColumns--;
                }
                if (this.addTrashIcon){
                    nbrColumns--;
                }
                nbrColumns -= sectionSubtotal.length;
                $cell.attr('colspan',nbrColumns);
            }else if(sectionSubtotal.indexOf(node.attrs.name)>=0){
                $cell.removeClass('o_hidden');
                return $cell;
            }
        }
        return $cell;
    },
});

basic_fields.NumericField.include({
/**
     * We want section and note to take the whole line (except handle and trash)
     * to look better and to hide the unnecessary fields.
     *
     * @override
     */
    init: function () {
        this._super.apply(this, arguments);
        this._setSectionWiseSubtotal();
    },
   /**
   @override
   **/
    _reset: function () {
        this._super.apply(this, arguments);
        this._setSectionWiseSubtotal();
    },

    _setSectionWiseSubtotal: function () {
    /** Function that calculate subtotal for each of the section in the order line.**/
        if (this.record.data['display_type'] === 'line_section') {
        var sequence = this.record.data.sequence;
        var id = this.record.data.id;
        if (this['__parentedParent'] && this.__parentedParent['state'] && this.__parentedParent.state['data']) {
            var all_rows = this.__parentedParent.state.data;
            var subtotal = 0.0;
            var self_found = false;
            for (var i = 0; i < all_rows.length; i++) {
                var row = all_rows[i].data;
                if (row.id == id) {
                    self_found = true;
                    continue;
                }
                if (self_found && row.sequence >= sequence) {
                    if (row.display_type === 'line_section' && row.id != id) {
                        break;
                    }
                    subtotal += row[this.name];
                }
            }
            this.value = subtotal;
        }
    }
    },
});
});
