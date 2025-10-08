odoo.define('whatsapp_mail_messaging.whatsapp_modal.js', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');
    var rpc = require('web.rpc');

    publicWidget.registry.deliveryDateToggl = publicWidget.Widget.extend({
        selector: '#ModalWhatsapp',
        events: {
            'change .custom-default': 'onclickCustomRadio',
            'change .default-default': 'onclickDefaultRadio',
            'change #myFormControl': 'onSelectChange',
            'click .btn-danger': 'onCloseButtonClick',
            'click .btn-success': 'onSendMessageClick',
        },
        start: function() {
            this._super.apply(this, arguments);
        },
        onclickCustomRadio: function () {
            document.getElementById("myFormControl").style.display = "none";
        },
        onclickDefaultRadio: function () {
            document.getElementById("myFormControl").style.display = "block";
            let data = ajax.jsonRpc('/whatsapp_message', {data:'data'})
            this.updateUI(data);
        },
        updateUI: function (data) {
            // Clear existing options
            var selectElement = document.getElementById("myFormControl");
            selectElement.innerHTML = '';
            // Add default option
            var defaultOption = document.createElement('option');
            defaultOption.textContent = 'Select the Template';
            selectElement.appendChild(defaultOption);

            // Add options from the data
            data.then((result) => {
                const messages = result.messages;
                messages.forEach((message) => {
                    var option = document.createElement('option');
                    option.value = message.id;
                    option.textContent = message.name;
                    option.setAttribute('data-message', message.message);
                    selectElement.appendChild(option);
                });
            })
        },
        onSelectChange: function () {
            var selectElement = document.getElementById("myFormControl");
            var textareaElement = document.getElementById("exampleFormControlTextarea1");
            var selectedOption = selectElement.options[selectElement.selectedIndex];
            var selectedMessage = selectedOption.getAttribute('data-message');
            // Update the textarea with the message from the selected option
            textareaElement.value = selectedMessage;
        },
        onCloseButtonClick: function () {
            //Closing the Modal
            document.getElementById("ModalWhatsapp").style.display = "none";
        },
        onSendMessageClick: function () {
            // Send Message to Whatsapp
            var textareaElement = document.getElementById("exampleFormControlTextarea1");
            var messageString = textareaElement.value;
            let data = ajax.jsonRpc('/mobile_number', {data:'data'})
            data.then((result) => {
                const mobile_num = result.mobile;
                mobile_num.forEach((mobile) => {
                    if (mobile_num && mobile_num.length > 0 && 'mobile_number' in mobile_num[0] && mobile_num[0].mobile_number) {
                        var mobileNumber = mobile_num[0].mobile_number;
                        // Construct the WhatsApp URL using the mobile number and messageString
                        var whatsappUrl = 'https://api.whatsapp.com/send?phone=' + mobileNumber + '&text=' + encodeURIComponent(messageString);
                        window.open(whatsappUrl, '_blank');
                    } else {
                        document.querySelector("#phoneMessage").style.display = "block";
                    }
                });
            })
        },
    });
});