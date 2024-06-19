/** @odoo-module **/
import { registerPatch } from '@mail/model/model_core';
import '@mail/models/composer_view';
import { _t } from "@web/core/l10n/translation";
import Dialog from 'web.Dialog';
import rpc from "web.rpc";

registerPatch({
    name: 'ComposerView',
    recordMethods: {
        /**cTo open the modal for chatgpt **/
        onClickGPT: function(){
            myModal.style.display = "block";
        },
        /** Function to get response from ChatGPT**/
        async _send_message(){
            var rpc = require('web.rpc');
            await rpc.query({
                model: 'res.config.settings',
                method: 'get_chat_gpt_key',
                args: [,],
            }).then(result => {
                this.api_key = result;
            });
            if (!this.api_key) {
                Dialog.alert(this, _t('Please Enter an API key'));
            } else {
                const myHeaders = new Headers();
                myHeaders.append("Content-Type", "application/json");
                myHeaders.append("Authorization", "Bearer " + this.api_key);
                const question = document.querySelector('.question_chat');
                const raw = JSON.stringify({
                    "model": "gpt-3.5-turbo",
                    "messages": [
                    {
                        "role": "user",
                        "content": question.value
                    }
                    ],
                    "temperature": 0.7
                });
                const requestOptions = {
                    method: "POST",
                    headers: myHeaders,
                    body: raw,
                    redirect: "follow"
                 };
                fetch("https://api.openai.com/v1/chat/completions", requestOptions)
                .then((response) => response.text())
                .then((result) => {
                    const obj = JSON.parse(result);
                    if (!obj['error']){
                        let area = obj.choices[0].message['content'];
                        const answer = document.querySelector('.answer_chat');
                        answer.value = area
                    }
                    else{
                        Dialog.alert(this, obj['error']['message']);
                    }
                });
            }
        },
        /** Function for passing the response to chatter**/
        _insert_message: function(){
            const insert_data = document.querySelector('.answer_chat');
            document.querySelector('.o_ComposerTextInput_textarea').value = insert_data.value
            const question = document.querySelector('.question_chat');
            question.value = ''
            insert_data.value = ''
            myModal.style.display = "none";
        },
        /** Function for closing the modal**/
        _close_modal: function(){
            const insert_data = document.querySelector('.answer_chat');
            const question = document.querySelector('.question_chat');
            question.value = ''
            insert_data.value = ''
            myModal.style.display = "none";
        }
    }
});
