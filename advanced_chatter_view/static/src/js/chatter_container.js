/** @odoo-module **/
import { Chatter } from "@mail/core/web/chatter";
import { patch } from "@web/core/utils/patch";
const { useRef } = owl;
//patch the class ChatterContainer to added the click function
patch(Chatter.prototype ,{
    setup(...args) {
        super.setup(...args);
        this.root = useRef("main_root")
        this.root1 = useRef("root")
    },
    // Click function of SendMessage button
    _onClickSendMessage(ev) {
        this.root.el.querySelector('#chatter_message').classList.remove("d-none");
        this.root.el.offsetParent.classList.add('chatter-remove-position')
        this.root.el.querySelector('.cross').classList.remove("d-none");
        this.root.el.querySelector('.o-mail-Chatter-content').classList.remove("d-none");
        this.root.el.querySelector('.o_ChatterTopbar_rightSection').classList.remove("d-none");
        this.root.el.querySelector('#send_message').classList.add("d-none");
        this.root.el.querySelector('#log_note').classList.add("d-none");
        this.root.el.querySelector('#active').classList.add("d-none");
    },
    //Click function for LogNote button
    _onClickLogNote(ev) {
        this.root.el.querySelector('#chatter_note').classList.remove("d-none");
        this.root.el.offsetParent.classList.add('chatter-remove-position')
        this.root.el.querySelector('.cross').classList.remove("d-none");
        this.root.el.querySelector('.o_ChatterTopbar_rightSection').classList.remove("d-none");
        this.root.el.querySelector('.o-mail-Chatter-content').classList.remove("d-none");
        this.root.el.querySelector('#send_message').classList.add("d-none");
        this.root.el.querySelector('#log_note').classList.add("d-none");
        this.root.el.querySelector('#active').classList.add("d-none");
    },
    //Click function for Active button
    _onClickActive(ev) {
        this.root.el.querySelector('#chatter_activity').classList.remove("d-none");
        this.root.el.offsetParent.classList.add('chatter-remove-position')
        this.root.el.querySelector('.cross').classList.remove("d-none");
        this.root.el.querySelector('.o_ChatterTopbar_rightSection').classList.remove("d-none");
        this.root.el.querySelector('.o-mail-Chatter-content').classList.remove("d-none");
        this.root.el.querySelector('#send_message').classList.add("d-none");
        this.root.el.querySelector('#log_note').classList.add("d-none");
        this.root.el.querySelector('#active').classList.add("d-none");
    },
    //Click function to close chatter
    _onClickCross(ev) {
        this.root.el.offsetParent.classList.remove('chatter-remove-position')
        this.root.el.querySelector('#chatter_activity').classList.add("d-none");
        this.root.el.querySelector('#chatter_note').classList.add("d-none");
        this.root.el.querySelector('#chatter_message').classList.add("d-none");
        this.root.el.querySelector('.o_ChatterTopbar_rightSection').classList.add("d-none");
        this.root.el.querySelector('.o-mail-Chatter-content').classList.add("d-none");
        this.root.el.querySelector('.cross').classList.add("d-none");
        this.root.el.querySelector('#send_message').classList.remove("d-none");
        this.root.el.querySelector('#log_note').classList.remove("d-none");
        this.root.el.querySelector('#active').classList.remove("d-none");
    },
});
