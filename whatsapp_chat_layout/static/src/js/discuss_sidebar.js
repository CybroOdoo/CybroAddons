/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { DiscussSidebar } from "@mail/components/discuss_sidebar/discuss_sidebar";
const { onMounted, useRef } = owl;
var rpc = require('web.rpc');
patch(DiscussSidebar.prototype, 'discuss_sidebar//  model: "res.users",ord-patch', {
setup() {
        this._super.apply();
        this.root = useRef("root")
        onMounted(this.sidebar)
    },
    sidebar(){
    var self = this
        rpc.query({//Call rpc to get current user image.
            model: "res.users",
            method: "get_user_image",
        }).then(function(result) {
        let image = document.createElement('div')
        image.innerHTML = '<img class="o_Composer_currentPartner rounded-circle o_object_fit_cover"style="margin-top: 21px;margin-left: 10px;width: 45px;height: 45px;"src="data:image/png;base64,' + result + '">'
        self.root.el.querySelector('#img').appendChild(image);
        });
    },
    _onClickMail(ev) {// Click function of mail button
        this.root.el.querySelector('.mail').classList.remove("d-none");
        this.root.el.querySelector('.channel').classList.add("d-none");
        this.root.el.querySelector('.chat').classList.add("d-none");
    },
    _onClickChat(ev) {// Click function of chat button
        this.root.el.querySelector('.chat').classList.remove("d-none");
        this.root.el.querySelector('.mail').classList.add("d-none");
        this.root.el.querySelector('.channel').classList.add("d-none");
    },
    _onClickChannel(ev) {// Click function of channel button
        this.root.el.querySelector('.channel').classList.remove("d-none");
        this.root.el.querySelector('.mail').classList.add("d-none");
        this.root.el.querySelector('.chat').classList.add("d-none");
    },
});