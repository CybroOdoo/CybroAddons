odoo.define('whatsapp_mail_messaging.whatsapp_modal.js', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');
    var ajax = require('web.ajax');

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
        var self = this;
            this._rpc({
                model: 'selection.messages',  // Your Odoo model
                method: 'search_read',  // Use search_read to retrieve data
                fields: ['name', 'message'],  // Specify the fields you want to retrieve
            }).then(function (data) {
                // Process the data received from the server

                self.updateUI(data);
            });
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
    data.forEach(function (record) {
        var option = document.createElement('option');
        option.value = record.id;
        option.textContent = record.name;
        option.setAttribute('data-message', record.message);  // Save the message as a data attribute
        selectElement.appendChild(option);
    });
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
    this._rpc({
        model: 'website',
        method: 'search_read',
        fields: ['mobile_number'],
    }).then(function (data) {
        // Process the data received from the server
if (data && data.length > 0 && 'mobile_number' in data[0] && data[0].mobile_number) {
    // Check if 'mobile_number' is present in the first item of the 'data' array and is not falsy
    var mobileNumber = data[0].mobile_number;
    // Construct the WhatsApp URL using the mobile number and messageString
    var whatsappUrl = 'https://api.whatsapp.com/send?phone=' + mobileNumber + '&text=' + encodeURIComponent(messageString);
    // Open the WhatsApp URL in a new tab or window
    window.open(whatsappUrl, '_blank');
} else {
    // If mobile number is not available or falsy, hide the element with id "phoneMessage"
    document.getElementById("phoneMessage").style.display = "block";
    // You might want to display a user-friendly error message on the UI
}
})
},

    });
});