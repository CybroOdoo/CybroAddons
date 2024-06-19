odoo.define('odoo_chatgpt_connector.chatgpt_search', function(require) {
    'use strict';
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');
    var core = require('web.core');
    var rpc = require('web.rpc');

    publicWidget.registry.QuestionInput = publicWidget.Widget.extend({
        selector: "#main_layout",
        events: {
            'change #question_input ': 'get_answer',
            'click #copy_content': 'copy',
        },
        /**
         * @constructor
         */
        init: function() {
            var api_key = "";
        },

        /* For getting the Answer of submitted question*/
        get_answer: async function(event) {
            $(this).prop("disabled", true);
            $('#result_area').val('');
            $('#result_area')[0].placeholder = "Loading.....";
            if (!this.api_key) {
                await rpc.query({
                    model: 'res.config.settings',
                    method: 'get_chat_gpt_key',
                    args: [,],
                }).then(result => {
                console.log(result);
                    this.api_key = result;
                });
            }
            var question = event.target.value;
            var myHeaders = new Headers();
            myHeaders.append("Content-Type", "application/json");
            myHeaders.append("Authorization", "Bearer " + this.api_key);

            var raw = JSON.stringify({
                "model": "gpt-3.5-turbo-instruct",
                "prompt": question,
                "temperature": 0,
                "max_tokens": 1000,
                "top_p": 1,
                "frequency_penalty": 0,
                "presence_penalty": 0,
            });

            var requestOptions = {
                method: 'POST',
                headers: myHeaders,
                body: raw,
                redirect: 'follow'
            };

            fetch("https://api.openai.com/v1/completions", requestOptions)
                .then(response => response.text())
                .then(result => {
                    const obj = JSON.parse(result);
                    let area = obj.choices[0].text;
                    $('#result_area').val(obj.choices[0].text.trim());
                })
                .catch(error => console.log('error', error));
        },
        /*For copy the Answer to the clipboard*/
        copy: function(event) {
            var textToCopy = $("#result_area").val();
            var tempTextarea = $('<textarea>');
            $('body').append(tempTextarea);
            tempTextarea.val(textToCopy).select();
            document.execCommand('copy');
            tempTextarea.remove();
        },
    });
});