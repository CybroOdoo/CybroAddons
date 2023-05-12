/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
const { onMounted } = owl;
var rpc = require('web.rpc');
var array = []
var int
//patch the ListRenderer template to store and view pinned records
patch(ListRenderer.prototype, 'pin-rec//  model: "pin.records",ord-patch', {
    setup() {
        this._super.apply();
        onMounted(this.pin)
    },
    pin(){
    var current_model = this.props.list.model.env.searchModel.resModel
    var table_row = $('.o_data_row')
    var row = this.props.list.records
    rpc.query({// rpc query to view pinned records in top of the table.
            model: "pin.records",
            method: "pin_record",
            args: [current_model],
        }).then(function (result) {
            for (var num=0;num<=table_row.length-1;num++){
                var row_id = row[num].resId
                for (var i=0;i<=result.length-1;i++){
                    array.push({'id':result[i].id})
                     if (row_id == result[i].id){
                         if(row[num].resModel == result[i].model){
                            table_row[num].style.background = result[i].color
                            table_row[num].parentNode.insertBefore(table_row[num],table_row[0])
                        }
                     }
                }
            }
        });
    },
    pin_record(ev,record){
        var row = $(event.target).parent().parent()[0]
        var num = 0
        _.each(array, function(line,index) {
            if(line.id == record.resId){
          row.style.background='white',
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
        row.style.background='#4AEBC8'
        }
        var self = this;
        rpc.query({//rpc query to store pinned records in database
            model: "pin.records",
            method: 'save_pin_record',
            args: [[parseInt(record.resId),record.resModel,row.style.background]],
        }).then(function (data) {
        });
    }
});
