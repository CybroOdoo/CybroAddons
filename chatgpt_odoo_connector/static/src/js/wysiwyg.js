/** @odoo-module **/
import Wysiwyg from 'web_editor.wysiwyg';
import { browser } from '@web/core/browser/browser';
import { _t } from 'web.core';
var Dialog = require('web.Dialog');
var core = require('web.core');
var QWeb = core.qweb;
var rpc = require('web.rpc');
import { OpenChatGPT } from "./open_chatgpt";
import { recordAudio } from "./recordAudio";
const { mount } = owl;
/* Appending new Category AI Tools, Chatgpt tool, and Speech-to-text tool in the powerbox options */
Wysiwyg.include({
    init: function (parent, options) {
        this._super.apply(this, arguments);
    },
    /* Function for adding new category and tool */
    _getPowerboxOptions: function (){
        const options = this._super();
        const { commands, categories } = options;
        const Category = {
            name: _t('AI Tools'),
            priority: 40
        };
        const itemSectionCommand = {
            category: _t('AI Tools'),
            name: _t('ChatGPT'),
            priority: 40,
            description: _t('Generate content with AI'),
            fontawesome: 'fa-magic',
            callback: this._openChatGPT.bind(this)
        };
        const itemSpeechToAudio = {
            category: _t('AI Tools'),
            name: _t('Speech-To-Text'),
            priority: 40,
            description: _t('Speech to text'),
            fontawesome: 'fa-microphone',
            callback: this._recordVoice.bind(this)
        };
        categories.push(Category);
        commands.push(itemSectionCommand);
        commands.push(itemSpeechToAudio);
        return options;
    },
    /* Function for mounting the element of chatgpt in the view */
    _openChatGPT: function () {
        var element = $('.o_web_client')[0];
        if (element) {
            const props = {rpc: rpc, self: this};
            mount(OpenChatGPT, element, {props: props});
        }
    },
    /* Function for mounting the element speech-to-text in the view */
    _recordVoice: function () {
        var element = $('.o_web_client')[0];
        if (element) {
            const props = {rpc: rpc, self: this};
            mount(recordAudio, element, {props: props});
        }
    },
});
