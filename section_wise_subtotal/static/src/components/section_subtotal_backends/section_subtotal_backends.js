/** @odoo-module
 * This module help us to calculate the section wise subtotal in
 * Sale order, Purchase order and Invoice.
 **/
import { SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend";
import { patch }  from "@web/core/utils/patch";

patch(SectionAndNoteListRenderer.prototype, 'SectionAndNoteListRenderer', {
    /*** The purpose of this patch is to allow sections in the one2many list
      primarily used on Sales Orders, Purchase Order and Invoices*/
    setup(){
    /** This function help to access the subtotal field in order line*/
        this._super(...arguments)
        this['subtotal_titleField'] = "price_subtotal"
    },

    isSectionOrNote(record=null) {
    /*Function  to calculate the subtotal in a section */
        if(this.record){
            if (this.record.data['display_type'] === 'line_section') {
                var sequence = this.record.data.sequence;
                var id = this.record.data.id;
                var all_rows = this.list.records;
                var subtotal = 0.0;
                var self_found = false;
                for (var i = 0; i < all_rows.length; i++) {
                    var row = all_rows[i].data;
                    if (row.id == id) {
                        self_found = true;
                        continue;
                    }
                    if (self_found && row.sequence >= sequence) {
                        if (row.display_type === 'line_section' && row.id != id){
                            break;
                        }
                        subtotal += row.price_subtotal;
                    }
                }
                this.record.data.price_subtotal = subtotal;
            }
        }
        record = record || this.record;
        return ['line_section', 'line_note'].includes(record.data.display_type);
    },

    /* Returns the class of subtotal to make it visible */
    getCellClass(column, record) {
        let classNames = this._super(column, record)
        return classNames + 'price_subtotal'
    },

    getColumns(record) {
    /*Check whether we select Line section or Line note and call
     the corresponding function*/
        const columns = this.state.columns;
        if (this.isSectionOrNote(record)) {
            if(record.data.display_type == 'line_note'){
                const columns = this.state.columns;
                return this.getSectionColumns(columns);
            }
            else{
                const columns = this.state.columns;
                return this.getSubtotalSectionColumns(columns);
            }
        }
        return columns;
    },

    getSubtotalSectionColumns(columns) {
    /*Function that allow to visible the subtotal field in order line*/
        const sectionCols = columns.filter((col) => col.widget === "handle" || col.type === "field" && col.name === this.subtotal_titleField || col.type === "field" && col.name === this.titleField);
        return sectionCols.map((col) => {
            if (col.name === this.titleField) {
                return { ...col, colspan: columns.length - sectionCols.length + 1 };
            } else {
                return { ...col };
            }
        });
    }
});
