/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { ListRenderer } from "@web/views/list/list_renderer";
const { onMounted } = owl;
var array = []
var int
//patch the ListRenderer template to store and view pinned records
patch(ListRenderer.prototype, {
    setup() {
        super.setup();
        this.orm = useService("orm");
        onMounted(this.pin)
    },
    async pin(){
    var current_model = this.props.list.model.env.searchModel.resModel
    var table_row = $('.o_data_row')
    var row = this.props.list.records
    var result = await this.orm.call('pin.records',
             'pin_record',[current_model])
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
        }
        if(num==0)
        {
        $($(event.target).parent().parent().parent()[0]).prepend(row)
        array.push({'id': record.resId})
        row.style.setProperty('--table-bg', '#4AEBC8');
        }
        var self = this;
        var result = await this.orm.call('pin.records',
             'save_pin_record',[[parseInt(record.resId),record.resModel,row.style.backgroundColor]])
        if (result){
    }
    }
});
