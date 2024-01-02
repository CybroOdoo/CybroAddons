odoo.define('advanced_chatter_view.chatter_container', function (require) {
//Added the click function in the class ChatterContainer
    'use strict';
    const ChatterContainer = require('mail/static/src/components/chatter_container/chatter_container.js');
    Object.assign(ChatterContainer.prototype, {
        _onClickSendMessage(ev) {// Click function of SendMessage button
            this.el.querySelector("#chatter_message").classList.remove("d-none");
            this.el.querySelector(".view").classList.remove("d-none");
            this.el.querySelector(".cross").classList.remove("d-none");
            this.el.querySelector(".o_ChatterTopbar_rightSection").classList.remove("d-none");
            this.el.querySelector('#send_message').classList.add("d-none");
            this.el.querySelector('#log_note').classList.add("d-none");
            this.el.querySelector('#active').classList.add("d-none");
        },
        _onClickLogNote(ev) {//Click function for LogNote button
            this.el.querySelector("#chatter_note").classList.remove("d-none");
            this.el.querySelector(".view").classList.remove("d-none");
            this.el.querySelector(".cross").classList.remove("d-none");
            this.el.querySelector(".o_ChatterTopbar_rightSection").classList.remove("d-none");
            this.el.querySelector('#send_message').classList.add("d-none");
            this.el.querySelector('#log_note').classList.add("d-none");
            this.el.querySelector('#active').classList.add("d-none");
        },
        _onClickActive(ev) {//Click function for Active button
            this.el.querySelector("#chatter_activity").classList.remove("d-none");
            this.el.querySelector(".view").classList.remove("d-none");
            this.el.querySelector(".cross").classList.remove("d-none");
            this.el.querySelector(".o_ChatterTopbar_rightSection").classList.remove("d-none");
            this.el.querySelector('#send_message').classList.add("d-none");
            this.el.querySelector('#log_note').classList.add("d-none");
            this.el.querySelector('#active').classList.add("d-none");
        },
        _onClickCross(ev) {//Click function to close chatter.
            this.el.querySelector('#chatter_activity').classList.add("d-none");
            this.el.querySelector("#chatter_note").classList.add("d-none");
            this.el.querySelector("#chatter_message").classList.add("d-none");
            this.el.querySelector(".view").classList.add("d-none");
            this.el.querySelector(".cross").classList.add("d-none");
            this.el.querySelector(".o_ChatterTopbar_rightSection").classList.add("d-none");
            this.el.querySelector('#send_message').classList.remove("d-none");
            this.el.querySelector('#log_note').classList.remove("d-none");
            this.el.querySelector('#active').classList.remove("d-none");
            if (this.el.querySelector('.chat')){
                this.el.querySelector('.chat').classList.add("d-none");
            }
        }
    });
    return ChatterContainer;
});
