/** @odoo-module **/
import { session } from "@web/session";
import { ListRenderer } from "@web/views/list/list_renderer";
import { patch } from "@web/core/utils/patch";
import { browser } from "@web/core/browser/browser";
import { useService } from "@web/core/utils/hooks";
const {onMounted} = owl;

patch(ListRenderer.prototype, 'custom_list_view/static/src/js/record_highlight.js', {
      setup(){
         this._super(...arguments)
        onMounted(() => {
        var tdElement = document.createElement('td');
        var thElement = document.createElement('th');
        thElement.innerText = "Sl No"
        thElement.style.width = "60px"
        var firstRow = $(this.__owl__.bdom.parentEl.querySelectorAll('.o_list_table')).find('thead tr').first();
        var secondRow = $(this.__owl__.bdom.parentEl.querySelectorAll('.o_list_footer')).find('tr').first();
        firstRow.prepend(thElement);
        secondRow.prepend(tdElement);
        });
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
