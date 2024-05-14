/** @odoo-module **/
import SystrayMenu from 'web.SystrayMenu';
import Widget from 'web.Widget';
import { _t } from "@web/core/l10n/translation";
import Dialog from 'web.Dialog';
var rpc = require('web.rpc');

var GoogleSearchWidget = Widget.extend({
    template: 'SearchSystray',
    events: {
        'keydown #search_text': '_onClick',
        'click #search_icon': '_onClick',
    },
    /**
     * @override
    */
    init: function () {
        this._super.apply(this, arguments);
    },
    _onClick: function (event) {
        // Get response from google based on the search value and display result on the template
        var input = this.$el.find('#search_text')[0];
        const resultsDiv = this.$el.find('.google_result')[0];
        if (event.key === "Enter" || !event.key && input.value.trim() !== '') {
            rpc.query({
                model: 'res.config.settings',
                method: 'google_search_config',
                args: [input.value],
            }).then(result => {
                if (!result) {
                    Dialog.alert(this, _t('Invalid Credentials'));
                }else if (result.error) {
                    Dialog.alert(this, _t(result.error));
                } else if (result === null) {
                    Dialog.alert(this, _t('Limit exceeded for Queries and Queries per day'));
                } else {
                    resultsDiv.innerHTML = '';
                    for (let i = 0; i < result.length; i++) {
                        const resultItem = document.createElement("div");
                        const titleText = document.createTextNode(result[i].title);
                        const titleElement = document.createElement("h2");
                        titleElement.classList.add("header")
                        titleElement.appendChild(titleText);
                        const linkElement = document.createElement("a");
                        linkElement.classList.add("link")
                        linkElement.href = result[i].link;
                        linkElement.textContent = result[i].link;
                        const snippetText = document.createTextNode(result[i].snippet);
                        const snippetElement = document.createElement("p");
                        snippetElement.classList.add("content")
                        snippetElement.appendChild(snippetText);
                        resultItem.appendChild(titleElement);
                        resultItem.appendChild(linkElement);
                        resultItem.appendChild(snippetElement);
                        resultsDiv.appendChild(resultItem);
                    }
                    resultsDiv.style.display = 'block';
                }
            });
        } else {
            resultsDiv.style.display = 'none';
        }
    }
});
SystrayMenu.Items.push(GoogleSearchWidget);
export default GoogleSearchWidget;
