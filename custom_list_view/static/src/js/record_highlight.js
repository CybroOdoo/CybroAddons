/** @odoo-module **/
import { session } from "@web/session";
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useService } from "@web/core/utils/hooks";

patch(ListRenderer.prototype, 'custom_list_view/static/src/js/record_highlight.js', {
      setup(){
         this._super(...arguments)
      },
      toggleRecordSelection(record) {
        var self = this;
        this._super.apply(this, arguments);
        var selectedRecord = $(event.target).closest('tr')
        if($(event.target).prop('checked')){
            selectedRecord.addClass('selected_record');
        } else {
            selectedRecord.removeClass('selected_record')
        }
      }
})
