/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from '@web/views/list/list_controller';

//For ORM Call
import { useService } from "@web/core/utils/hooks";


const { useRef, onPatched, onMounted, useState } = owl;

//Patching
patch(ListRenderer.prototype, 'list-color-patch', {
    setup() {
        this._super.apply();
        this.orm = useService("orm");
//        PATH OF CORRESPONDING MODEL
//        var current_model = this.props.list.model.env.searchModel.resModel
        onMounted(this.color)
    },


    color_pick(ev,record){
        var color = ev.target.value
        var res_id = record.resId
        var res_model = record.resModel

                                  //ORM Call

        this.orm.call("color.picker","get_color_picker_model_and_id",[],{
            record_id: res_id,
            model_name: res_model,
            record_color: color,
        }).then(function(data){


        })


        ev.target.parentNode.parentNode.style.backgroundColor = color
    },


//Call from onMounted
    color(){
      var current_model = this.props.list.model.env.searchModel.resModel
      var tr_list = $('.o_data_row')
      var current_tr;


        this.orm.call("color.picker","search_read",[],{
          domain: [
                ['res_model', '=',current_model],

            ],

        }).then(function(data){
        for(var i=0;i<tr_list.length;i++){
        current_tr = tr_list[i].children[1].dataset.id

         for(var j=0;j<data.length;j++){
         if(current_tr == data[j].record_id){
         tr_list[i].style.backgroundColor = data[j].color


         }

         }
        }

        })

    },

})
