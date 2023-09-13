/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { ListRenderer } from "@web/views/list/list_renderer";
import { ListController } from '@web/views/list/list_controller';
//For ORM Call
import { useService } from "@web/core/utils/hooks";
const { useRef, onPatched, onMounted, useState,onWillUpdateProps } = owl;
//Patching
patch(ListRenderer.prototype, 'list-color-patch', {
    setup() {
        if (this.constructor.name == 'SectionAndNoteListRenderer') {
        // Call method for removing color picking field from one2many
            onMounted(() => {
                this.__owl__.bdom.el.children[0].children[1].childNodes.forEach((item) => {
                    if (item.nodeName != "#text"){
                        if(!item.attributes.length == 0){
                            var list_one2many = item.children[1];
                            list_one2many.remove();
                        }
                    }
                })
            })
        }
        this._super.apply();
        this.orm = useService("orm");
        onMounted(this.color);
        if (this.constructor.name == 'SectionAndNoteListRenderer') {
        // Call method for removing color picking field from one2many
            onPatched(()=>{
                this.__owl__.bdom.el.children[0].children[1].childNodes.forEach((item) => {
                    if (item.nodeName != "#text"){
                        if(!item.attributes.length == 0){
                            var list_one2many = item.children[1];
                            list_one2many.remove();
                        }
                    }
                })
            });
        }
        onPatched(()=>{
            this.color()
        });
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
        var self = this;
        this.orm.call("color.picker","search_read",[],{
            domain: [
                ['res_model', '=',current_model],
            ],
        }).then(function(data){
            Array.prototype.forEach.call(tr_list, function(tr) {
                data.forEach((item) => {
                    if (tr.firstChild.nextElementSibling.dataset.id == item.record_id) {
                        tr.style.backgroundColor = item.color
                    }
                });
            });
        })
    },
})