/** @odoo-module **/
import { registerInstancePatchModel } from '@mail/model/model_core';
import { ComposerTextInput } from '@mail/components/composer_text_input/composer_text_input';
import rpc from 'web.rpc';
import {patch} from 'web.utils';
/* Add new functionality on keyup of textarea */
patch(ComposerTextInput.prototype, "my patch", {
        _onKeydownTextarea(ev){
            let autoCompleteTextAreaEl = this.el.querySelector('#autoCompleteText');
            let userTextAreaEl = this.el.querySelector('#userInputText');
            var UserInput = userTextAreaEl.value;
            rpc.query({
                model: 'mail.message',
                method: 'get_message',
            }).then(function (data) {
                    if (UserInput !== '/') {
                        /*Matching sentences or words are taken from the list */
                        UserInput = UserInput.replace(new RegExp("\\\\", "g"), "\\\\");
                        const matcher = new RegExp(`^${UserInput}`, 'g');
                        var filter_list = data.filter(word => word.match(matcher));
                        filter_list.sort();
                        if (filter_list[0] == null) {
                            autoCompleteTextAreaEl.value = ' ';
                        }
                        else {
                            autoCompleteTextAreaEl.value = filter_list[0];
                        }
                        if (UserInput == '') {
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
      if (!this.composerView) {
            return;
        }
        switch (ev.key) {
            case 'Escape':
                if (this.composerView.hasSuggestions) {
                    ev.preventDefault();
                    this.composerView.closeSuggestions();
                    markEventHandled(ev, 'ComposerTextInput.closeSuggestions');
                }
                break;
            // UP, DOWN, TAB: Prevent moving cursor if navigation in mention suggestions
            case 'ArrowUp':
            case 'PageUp':
            case 'ArrowDown':
            case 'PageDown':
            case 'Home':
            case 'End':
            case 'Tab':
                if (this.composerView.hasSuggestions) {
                    // We use preventDefault here to avoid keys native actions but actions are handled in keyUp
                    ev.preventDefault();
                }
                break;
            // ENTER: Submit the message only if the dropdown mention proposition is not displayed
            case 'Enter':
                this._onKeydownTextareaEnter(ev);
                break;
        }
    },
    _onKeyupTextarea(ev){
            let autoCompleteTextAreaEl = this.el.querySelector('#autoCompleteText');
            let userTextAreaEl = this.el.querySelector('#userInputText');
            var UserInput = userTextAreaEl.value;
            rpc.query({
                model: 'mail.message',
                method: 'get_message',
            }).then(function (data) {
                    if (UserInput !== '/') {
                        /*Matching sentences or words are taken from the list */
                        UserInput = UserInput.replace(new RegExp("\\\\", "g"), "\\\\");
                        const matcher = new RegExp(`^${UserInput}`, 'g');
                        var filter_list = data.filter(word => word.match(matcher));
                        filter_list.sort();
                        if (filter_list[0] == null) {
                            autoCompleteTextAreaEl.value = ' ';
                        }
                        else {
                            autoCompleteTextAreaEl.value = filter_list[0];
                        }
                        if (UserInput == '') {
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
            if (!this.composerView) {
            return;
        }
        switch (ev.key) {
            case 'Escape':
                // Already handled in _onKeydownTextarea, break to avoid default
                break;
            // ENTER, HOME, END, UP, DOWN, PAGE UP, PAGE DOWN, TAB: check if navigation in mention suggestions
            case 'Enter':
                if (this.composerView.hasSuggestions) {
                    this.composerView.insertSuggestion();
                    this.composerView.closeSuggestions();
                    this.composerView.update({ doFocus: true });
                }
                break;
            case 'ArrowUp':
            case 'PageUp':
                if (ev.key === 'ArrowUp' && !this.composerView.hasSuggestions &&
                 !this.composerView.composer.textInputContent &&
                  this.composerView.threadView) {
                    this.composerView.threadView.startEditingLastMessageFromCurrentUser();
                    break;
                }
                if (this.composerView.hasSuggestions) {
                    this.composerView.setPreviousSuggestionActive();
                    this.composerView.update({ hasToScrollToActiveSuggestion: true });
                }
                break;
            case 'ArrowDown':
            case 'PageDown':
                if (ev.key === 'ArrowDown' && !this.composerView.hasSuggestions
                 && !this.composerView.composer.textInputContent &&
                 this.composerView.threadView) {
                    this.composerView.threadView.startEditingLastMessageFromCurrentUser();
                    break;
                }
                if (this.composerView.hasSuggestions) {
                    this.composerView.setNextSuggestionActive();
                    this.composerView.update({ hasToScrollToActiveSuggestion: true });
                }
                break;
            case 'Home':
                if (this.composerView.hasSuggestions) {
                    this.composerView.setFirstSuggestionActive();
                    this.composerView.update({ hasToScrollToActiveSuggestion: true });
                }
                break;
            case 'End':
                if (this.composerView.hasSuggestions) {
                    this.composerView.setLastSuggestionActive();
                    this.composerView.update({ hasToScrollToActiveSuggestion: true });
                }
                break;
            case 'Tab':
                if (this.composerView.hasSuggestions) {
                    if (ev.shiftKey) {
                        this.composerView.setPreviousSuggestionActive();
                        this.composerView.update({ hasToScrollToActiveSuggestion: true });
                    } else {
                        this.composerView.setNextSuggestionActive();
                        this.composerView.update({ hasToScrollToActiveSuggestion: true });
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
                // Prevent modifier keys from resetting the suggestion state
                break;
            // Otherwise, check if a mention is typed
            default:
                this.saveStateInStore();
        }
    },
});