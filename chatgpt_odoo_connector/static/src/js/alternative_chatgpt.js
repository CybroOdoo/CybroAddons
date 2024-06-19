odoo.define('chatgpt_odoo_connector.alternative_chatgpt', function (require) {
    'use strict';
    var Widget = require('web.Widget');
    var rpc = require('web.rpc');
    /* Extending the widget */
    var AlternativeChatGPT = Widget.extend({
        template: 'alternativeChatGPT',
        events: {
            'click .alterButton': '_onClick',
            'click .Replace': '_onClickReplace',
            'click .Cancel': '_onClickCancel',
        },
        init: function(parent, options) {
            this._super(parent);
            $(document).on('click', this._onOutSideClick.bind(this));
        },
        start: function() {
            var self = this;
            this._super.apply(this, arguments);
        },
        /* Function for clicking the buttons for shortening, lengthening and rephrasing the content */
        _onClick: function(event){
            var dataValue = event.target.getAttribute('data-value');
            var message = this.__parentedParent.__parentedParent.el.innerText
            this.response = rpc.query({
                model: 'open.chatgpt',
                method: 'edit_content',
                args: [message,dataValue],
            }).then((response) => {
                document.getElementById('response').value = response;
            })
        },
        /* Function for inserting the created response into the description field */
        _onClickReplace: function(){
            var new_content = document.getElementById('response').value;
            if (new_content.trim()){
                this.__parentedParent.__parentedParent.el.innerText = new_content
                this._onClickCancel();
            }
        },
        /* Function for closing the widget while clicking outside */
        _onOutSideClick: function(ev){
            var element = document.querySelector('.popChatGPTAlter');
            var element_button = document.getElementsByClassName('chatgpt');
            var isClickInsideElementButton = Array.from(element_button).some(button => button.contains(ev.target));
            if (element && !element.contains(ev.target) && !isClickInsideElementButton){
                this._onClickCancel();
            }
        },
        /* Function for closing */
        _onClickCancel: function(){
            this.destroy()
        }
    });
    return AlternativeChatGPT;
});
