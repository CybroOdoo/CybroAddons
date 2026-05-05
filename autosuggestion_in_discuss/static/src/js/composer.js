/** @odoo-module **/
import { Composer } from "@mail/core/common/composer";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import {toRaw} from "@odoo/owl";
import { isEventHandled, markEventHandled} from "@web/core/utils/misc";

patch(Composer.prototype, {
        setup() {
            super.setup();
            },
        onKeydown(ev) {
        const composer = toRaw(this.props.composer);
        const el = this.ref.el;
        const self = this
            /*While keydown works on a keyboard this function takes the value in the input area and
            compares it with the ones in the list and finds a proper match.On clicking the tab the full
            sentence or word will be available.*/
            let autoCompleteTextAreaEl = document.querySelector('#autoCompleteText');
            let userTextAreaEl = document.querySelector('#userInputText');
            var value = userTextAreaEl.value;
            rpc('/web/dataset/call_kw', {
                model: 'mail.message',
                method: 'get_message',
                args: [],
                kwargs: {},
            }).then(function (data) {
                    var search_terms = data
                    if (value !== '/') {
                        /*Matching sentences or words are taken from the list search_terms*/
                        //Escape special characters from regular expression to avoid errors
                        value = value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
                        const matcher = new RegExp(`^${value}`, 'g');
                        var filter_list = search_terms.filter(word => word.match(matcher));
                        filter_list.sort();
                        if (filter_list[0] == null) {
                            autoCompleteTextAreaEl.value = ' ';
                        }
                        else {
                            autoCompleteTextAreaEl.value = filter_list[0];
                        }
                        if (value == '') {
                            autoCompleteTextAreaEl.value = " ";
                        }
                        switch (ev.key) {
                            case 'Tab':
                            if (filter_list[0]){
                                    userTextAreaEl.value = filter_list[0];
                                    // composer.text = filter_list[0];
                                    autoCompleteTextAreaEl.value = ' ';
                                    el.focus();
                                    break;
                                }
                            case ' ':
                                autoCompleteTextAreaEl.value = ' ';
                                break;
                            case 'Enter':
                                autoCompleteTextAreaEl.value = ' ';
                                if (isEventHandled(ev, "NavigableList.select") || !self.state.active) {
                                    ev.preventDefault();
                                    return;
                                }
                                const shouldPost = self.props.mode === "extended" ? ev.ctrlKey : !ev.shiftKey;
                                if (!shouldPost) {
                                    return;
                                }
                                ev.preventDefault(); // to prevent useless return
                                if (composer.message) {
                                    self.editMessage();
                                } else {
                                    self.sendMessage();
                                }
                                break;
                            case "Escape":
                                if (isEventHandled(ev, "NavigableList.close")) {
                                    return;
                                }
                                if (self.props.onDiscardCallback) {
                                   self.props.onDiscardCallback();
                                    markEventHandled(ev, "Composer.discard");
                                }
                                break;
                                case 'ArrowRight':
                                if (filter_list[0]){
                                    userTextAreaEl.value = filter_list[0];
                                    autoCompleteTextAreaEl.value = ' ';
                                    break;
                                }
                        }
                    }
            });
        },

        onKeyupTextarea(ev) {
            /*While keyup works on a keyboard this function takes the value in the input area and
             compares it with the ones in the list and finds a proper match.While using onKeyupTextarea()
             the value from the text area will be available without  any delay.*/
            let autoCompleteTextAreaEl = document.querySelector('#autoCompleteText');
            let userTextAreaEl = document.querySelector('#userInputText');
            var value = userTextAreaEl.value;
            rpc('/web/dataset/call_kw', {
                model: 'mail.message',
                method: 'get_message',
                args: [],
                kwargs: {},
                }).then(function (data) {
                    var search_terms = data
                    if (value !== '/') {
                        /*Matching sentences or words are taken from the list search_terms*/
                        //Escape special characters from regular expression to avoid errors
                        value = value.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&");
                        const matcher = new RegExp(`^${value}`, 'g');
                        var filter_list = search_terms.filter(word => word.match(matcher));
                        filter_list.sort();
                        if (filter_list[0] == null) {
                            autoCompleteTextAreaEl.value = ' ';
                        }
                        else {
                            autoCompleteTextAreaEl.value = filter_list[0];
                        }
                        if (value == '') {
                            autoCompleteTextAreaEl.value = " ";
                        }
                    }
                })
                },
    });
