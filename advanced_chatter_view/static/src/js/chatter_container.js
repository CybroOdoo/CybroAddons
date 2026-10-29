/** @odoo-module **/
import { Chatter } from "@mail/chatter/web_portal_project/chatter";
import { patch } from "@web/core/utils/patch";

patch(Chatter.prototype, {
    setup(...args) {
        super.setup(...args);
        this.state.isAdvChatterOpen = false;
        this.state.advChatterFilter = null;
    },

    // Click function of SendMessage button
    _onClickSendMessage() {
        this.state.isAdvChatterOpen = true;
        this.state.advChatterFilter = "message";
        this.toggleComposer("message");
    },

    // Click function for LogNote button
    _onClickLogNote() {
        this.state.isAdvChatterOpen = true;
        this.state.advChatterFilter = "note";
        this.toggleComposer("note");
    },

    // Click function for Active (Activities) button
    _onClickActive() {
        this.state.isAdvChatterOpen = true;
        this.state.advChatterFilter = "activity";
        if (this.state.composerType) {
            this.toggleComposer(false);
        }
    },

    // Click function to close chatter
    _onClickCross() {
        this.state.isAdvChatterOpen = false;
        this.state.advChatterFilter = null;
        if (this.state.composerType) {
            this.toggleComposer(false);
        }
    },
});
