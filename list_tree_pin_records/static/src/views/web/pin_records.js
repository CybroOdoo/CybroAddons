import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
var array = []
var int

//Patching ListRenderer
patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        this.actionService = useService("action"); 
        this.orm = useService("orm");
        onMounted(() => {
        this.addPinHeader();
        this.addFooterPlaceholder();
            setTimeout(() => {

                this.pin();
            }, 200);
        });
    },

    addPinHeader() {

        if (this.props.list.isEmbedded) {
            return;
        }

        const table = this.tableRef?.el;
        if (!table) return;
         const isX2Many = table.closest(".o_field_x2many_list");

        if (isX2Many) {
            return;
        }
        const isSearchMore = table.closest(".o_select_create_dialog_content");
        if (isSearchMore) {
            return;
        }


        const headerRow = table.querySelector("thead tr");
        if (!headerRow) return;

        if (headerRow.querySelector(".o_pin_column")) {
            return;
        }

        const th = document.createElement("th");
        th.className = "o_pin_column";
        th.style.width = "40px";

        const icon = document.createElement("i");
        icon.className = "fa fa-thumb-tack";

        th.appendChild(icon);

        const selector = headerRow.querySelector(".o_list_record_selector");

        if (selector) {
            selector.insertAdjacentElement("beforebegin", th);
        } else {
            headerRow.insertAdjacentElement("afterbegin", th);
        }
    },
    addFooterPlaceholder() {

        const table = this.tableRef?.el;
        if (!table) return;

        const footerRow = table.querySelector("tfoot tr");

        if (!footerRow) return;

        if (footerRow.querySelector(".o_pin_footer")) {
            return;
        }

        const td = document.createElement("td");
        td.className = "o_pin_footer";

        footerRow.insertAdjacentElement("afterbegin", td);

    },
//    pin function to pin records
    async pin(){
        if (!this.props.list.records || this.props.list.isEmbedded ||
            this.tableRef.el.closest(".o_field_x2many_list") ||
            this.tableRef.el.closest(".o_select_create_dialog_content")) {
            return;
        }
        var current_model = this.props.list.model.env.searchModel.resModel
        var table_row = $('.o_data_row')
        var row = this.props.list.records
        var result = await this.orm.call('pin.records', 'pin_record',[current_model])
        if (result){
            for (var num=0;num<=table_row.length-1;num++){
                var row_id = row[num].resId
                for (var i=0;i<=result.length-1;i++){
                    array.push({'id':result[i].id})
                     if (row_id == result[i].id){
                         if(row[num].resModel == result[i].model){
                            table_row[num].style.setProperty('--table-bg', '#4AEBC8');
                            table_row[num].parentNode.insertBefore(table_row[num],table_row[0])
                        }
                     }
                }
            }
        };
    },
    async pin_record_details(ev,record){
        var row = $(event.target).parent().parent()[0]
        var num = 0
        array.forEach(function(line,index){
            if(line.id == record.resId){
                row.style.setProperty('--table-bg', 'white');
                int = index
                num = 1
            }
        });
        if(num==1){
            array.splice(int,1)
            this.actionService.doAction('soft_reload');
        }
        if(num==0) {
            $($(event.target).parent().parent().parent()[0]).prepend(row)
            array.push({'id': record.resId})
            row.style.setProperty('--table-bg', '#4AEBC8');
        }
        var self = this;
        var result = await this.orm.call('pin.records', 'save_pin_record',[[parseInt(record.resId),record.resModel,row.style.backgroundColor]])
    }
});
