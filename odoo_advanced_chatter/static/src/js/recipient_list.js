/** @odoo-module **/
import { FollowerList } from "@mail/core/web/follower_list";
import { patch } from "@web/core/utils/patch";
import { useState } from "@odoo/owl";
//----select the followers from the list
patch(FollowerList.prototype, {
    setup() {
    super.setup();
        this.state = useState({
            id:[]
        });
    },
    async check(ev, follower){
    //-----To include the newly selected followers into recipients list
        var index = this.state.id.indexOf(follower.partner.id)
        if (this.state.id.includes(follower.partner.id)){
            this.state.id.splice(index, 1)
        }
        else{
            this.state.id.push(follower.partner.id)
        }
        this.threadService.check = this.state.id
    }
})
