/** @odoo-module **/

import { Dropdown } from "@web/core/dropdown/dropdown";
import { DropdownItem } from "@web/core/dropdown/dropdown_item";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
const { useRef, onMounted } = owl;
import Dialog from 'web.Dialog';
import rpc from "web.rpc";
let chatHistory = [];
export class ChatGpt extends Component {
    /**
       * @Extends Component
    */
    setup() {
           var api_key = "";
           this.question = useRef("Question")
           this.chat = useRef("Chat")
           this.answer = useRef("Answer")
           this.body = useRef("body")
           super.setup(...arguments);
           onMounted(() => {
                   this.question.el.value = this.props.question || '';
                   this.chat.el.value = this.props.chat || '';
                   this.answer.el.value = this.props.chat || '';
                   this.body.el.value = this.props.body || '';
           });
    }
    async _chat_gpt(ev) {
     //Function to access chat gpt from systray
           var rpc = require('web.rpc');
           this.api_key =  await rpc.query({
               model: 'ir.config_parameter',
               method: 'get_param',
               args: ['odoo_chat_gpt.api_key'],
           });
           if (!this.api_key) {
               Dialog.alert(this, _t('Please select an API key'));
           }
           else {
                   this.body.el.style.display = "block";
           }
        const messageInput =  this.question.el;
        messageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                this._send_message();
            }
        });
    }
    async _send_message(ev) {
          // Function to get response from ChatGPT
          var self = this;
          const value = this.question.el.value;
          const question = this.chat.el.textContent = value;
          this.question.el.value = '';
          // Clear the previous answer
          this.answer.el.textContent = '';
          var myHeaders = new Headers();
          myHeaders.append('Content-Type', 'application/json');
          myHeaders.append('Authorization', 'Bearer ' + this.api_key);
          var raw = JSON.stringify({
            model: 'text-davinci-003',
            prompt: value,
            temperature: 0,
            max_tokens: 1000,
            top_p: 1,
            frequency_penalty: 0,
            presence_penalty: 0,
          });
          var requestOptions = {
            method: 'POST',
            headers: myHeaders,
            body: raw,
            redirect: 'follow',
          };

          // Fetch data from the URL
          fetch('https://api.openai.com/v1/completions', requestOptions)
            .then((response) => response.text())
            .then((result) => {
              const obj = JSON.parse(result);
              let area = obj.choices[0].text;
              const answer = this.answer.el.textContent = area;
              chatHistory.push({ question: value, answer: area });
          });
    }

    async _close() {
             //Function to close the screen
             this.body.el.style.display = "none";
             this.question.el.value = '';
             this.chat.el.textContent = '';
             this.answer.el.textContent = '';
    }
}
ChatGpt.template = "ChatGptSystray";
ChatGpt.components = { Dropdown, DropdownItem };
ChatGpt.props = {};
export const systrayItem = {
    Component: ChatGpt,
};
registry.category("systray").add("ChatGpt", systrayItem, { sequence: 0 });
