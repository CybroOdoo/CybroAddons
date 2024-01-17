/** @odoo-module **/
import { Component } from "@odoo/owl";
import { mount } from "@odoo/owl";
import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { PosMsgView } from "./pos_msg_view"
import { useRef} from "@odoo/owl";

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.message = useRef('root')
        },
    onClick(ev) {
        if($(".pos_systray_template").length == 0){
            this.schedule_dropdown = mount(PosMsgView, document.body)
        }else if($(".pos_systray_template").length > 0){
            this.schedule_dropdown.then(function(res){
                res.__owl__.remove()
            })
        }
    },
});
