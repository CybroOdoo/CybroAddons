/** @odoo-module **/
import publicWidget from '@web/legacy/js/public/public_widget';
import { _t } from "@web/core/l10n/translation";
publicWidget.registry.QuestionInput = publicWidget.Widget.extend({
    selector: "#main_layout",
    events: {
        'click #send_button': 'get_answer',
        'click #copy_content': 'copy',
    },
    /**
     * @constructor
     */
    init: function() {
        this._super(...arguments);
        this.orm = this.bindService("orm");
        this.notification = this.bindService("notification");
        this.api_key = "";
    },
    /* For getting the Answer of submitted question */
    get_answer: async function(event) {
        $(event.currentTarget).prop("disabled", true);
        $('#result_area').val('');
        $('#result_area')[0].placeholder = "Loading.....";
        if (!this.api_key) {
            await this.orm.call(
                "ir.config_parameter", "get_param", ["odoo_chatgpt_connector.api_key"]
            ).then(result => {
                this.api_key = result;
            });
        }
        var question = $('#question_input').val();
        if (!question) {
            $('#result_area')[0].placeholder = "Please drop your question";
            this.notification.add(
                _t("Please drop your question"),
                { type: 'danger', sticky: false },
            )
            $(event.currentTarget).prop("disabled", false);
            return;
        }
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
            .then(response => response.json())
            .then(result => {
                let area = result.choices[0].text;
                $('#result_area').val(area.trim());
                $(event.currentTarget).prop("disabled", false);
            })
            .catch(error => {
                $('#result_area')[0].placeholder = "Couldn't fetch";
                this.notification.add(
                _t("Couldn't connect to OpenAI server please check your Credentials"),
                { type: 'danger', sticky: false },
            )
                $(event.currentTarget).prop("disabled", false);
            });
    },
    /* For copying the Answer to the clipboard */
    copy: function(event) {
        var textToCopy = $("#result_area").val();
        var tempTextarea = $('<textarea>');
        $('body').append(tempTextarea);
        tempTextarea.val(textToCopy).select();
        document.execCommand('copy');
        tempTextarea.remove();
    },
});
