/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
import '@mail/models/composer_view';
var rpc = require('web.rpc');


registerPatch({
    name: 'ComposerView',
    recordMethods: {
        onKeydown(ev) {
            /*While keydown works on a keyboard this function takes the value in the input area and
            compares it with the ones in the list and finds a proper match.On clicking the tab the full
            sentence or word will be available.*/
            let autoCompleteTextAreaEl = document.querySelector('#autoCompleteText');
            let userTextAreaEl = document.querySelector('#userInputText');
            var value = userTextAreaEl.value;
            rpc.query({
                model: 'mail.message',
                method: 'get_message',
            })
                .then(function (data) {
                    var search_terms = data
                    if (value !== '/') {
                        /*Matching sentences or words are taken from the list search_terms*/
                        value = value.replace(new RegExp("\\\\", "g"), "\\\\");
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
                                userTextAreaEl.value = filter_list[0];
                                autoCompleteTextAreaEl.value = ' ';
                            case ' ':
                                autoCompleteTextAreaEl.value = ' ';
                            case 'Enter':
                                autoCompleteTextAreaEl.value = ' ';
                        }
                    }
                })
            if (ev.key === 'Escape') {
                if (isEventHandled(ev, 'ComposerTextInput.closeSuggestions')) {
                    return;
                }
                if (isEventHandled(ev, 'Composer.closeEmojisPopover')) {
                    return;
                }
                ev.preventDefault();
                this.discard();
            }
        },
        onKeyupTextarea(ev) {
            /*While keyup works on a keyboard this function takes the value in the input area and
             compares it with the ones in the list and finds a proper match.While using onKeyupTextarea()
             the value from the text area will be available without  any delay.*/
            if (!this.exists()) {
                return;
            }
            let autoCompleteTextAreaEl = document.querySelector('#autoCompleteText');
            let userTextAreaEl = document.querySelector('#userInputText');
            var value = userTextAreaEl.value;
            rpc.query({
                model: 'mail.message',
                method: 'get_message',
            })
                .then(function (data) {
                    var search_terms = data
                    if (value !== '/') {
                        /*Matching sentences or words are taken from the list search_terms*/
                        value = value.replace(new RegExp("\\\\", "g"), "\\\\");
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
                            case 'ArrowRight':
                                userTextAreaEl.value = filter_list[0];
                                autoCompleteTextAreaEl.value = ' ';
                            case ' ':
                                autoCompleteTextAreaEl.value = ' ';
                            case 'Enter':
                                autoCompleteTextAreaEl.value = ' ';
                        }
                    }
                })
            switch (ev.key) {
                case 'Escape':
                    // already handled in _onKeydownTextarea, break to avoid default
                    break;
                // ENTER, HOME, END, UP, DOWN, PAGE UP, PAGE DOWN, TAB: check if navigation in mention suggestions
                case 'Enter':
                    if (this.hasSuggestions) {
                        this.insertSuggestion();
                        this.closeSuggestions();
                        this.update({ doFocus: true });
                    }
                    break;
                case 'ArrowUp':
                case 'PageUp':
                    if (ev.key === 'ArrowUp' && !this.hasSuggestions && !this.composer.textInputContent && this.threadView) {
                        this.threadView.startEditingLastMessageFromCurrentUser();
                        break;
                    }
                    if (this.composerSuggestionListView) {
                        this.composerSuggestionListView.setPreviousSuggestionViewActive();
                        this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                    }
                    break;
                case 'ArrowDown':
                case 'PageDown':
                    if (ev.key === 'ArrowDown' && !this.hasSuggestions && !this.composer.textInputContent && this.threadView) {
                        this.threadView.startEditingLastMessageFromCurrentUser();
                        break;
                    }
                    if (this.composerSuggestionListView) {
                        this.composerSuggestionListView.setNextSuggestionViewActive();
                        this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                    }
                    break;
                case 'Home':
                    if (this.composerSuggestionListView) {
                        this.composerSuggestionListView.setFirstSuggestionViewActive();
                        this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                    }
                    break;
                case 'End':
                    if (this.composerSuggestionListView) {
                        this.composerSuggestionListView.setLastSuggestionViewActive();
                        this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                    }
                    break;
                case 'Tab':
                    if (this.composerSuggestionListView) {
                        if (ev.shiftKey) {
                            this.composerSuggestionListView.setPreviousSuggestionViewActive();
                            this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                        } else {
                            this.composerSuggestionListView.setNextSuggestionViewActive();
                            this.composerSuggestionListView.update({ hasToScrollToActiveSuggestionView: true });
                        }
                    }
                    break;
                case 'Alt':
                case 'AltGraph':
                case 'CapsLock':
                case 'Control':
                case 'Fn':
                case 'FnLock':
                case 'Hyper':
                case 'Meta':
                case 'NumLock':
                case 'ScrollLock':
                case 'Shift':
                case 'ShiftSuper':
                case 'Symbol':
                case 'SymbolLock':
                    // prevent modifier keys from resetting the suggestion state
                    break;
                // Otherwise, check if a mention is typed
                default:
                    this.saveStateInStore();
            }
        },
    }
});
