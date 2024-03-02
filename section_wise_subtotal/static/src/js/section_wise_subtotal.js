/** @odoo-module **/
import {SectionAndNoteListRenderer } from "@account/components/section_and_note_fields_backend/section_and_note_fields_backend"
import { patch } from "@web/core/utils/patch";

patch(SectionAndNoteListRenderer.prototype,{
    /*** The purpose of this patch is to allow sections in the one2many list
      primarily used on Sales Orders, Purchase Order and Invoices*/
    setup(){
    /** This function help to access the subtotal field in order line*/
        super.setup();
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
                    if (row.sequence == sequence) {
                        self_found = true;
                        continue;
                    }
                    if (self_found && row.sequence >= sequence) {
                        if (row.display_type === 'line_section' && row.sequence != sequence){
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
    getCellClass(column, record) {
    /*Help to hide the fields in order line except Description and Subtotal*/
        var classNames = super.getCellClass(column, record);
        if (this.isSectionOrNote(record) && column.widget !== "handle" && column.name !== this.titleField && column.name !== this.subtotal_titleField) {
            return `${classNames} o_hidden`;
        }
        if (column.name == 'price_subtotal' && classNames.includes("o_hidden")){
            classNames = classNames.replace("o_hidden", "").trim();
        }
        return classNames;
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
