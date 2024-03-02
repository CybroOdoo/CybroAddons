/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { useService } from "@web/core/utils/hooks";
import { jsonrpc } from "@web/core/network/rpc_service";
// Define a new widget named 'deliveryDateToggl' that extends the 'publicWidget.Widget' class
publicWidget.registry.deliveryDateToggl = publicWidget.Widget.extend({
    selector: '#ModalWhatsapp',
    events: {
        'change .custom-default': 'onclickCustomRadio',
        'change .default-default': 'onclickDefaultRadio',
        'change #myFormControl': 'onSelectChange',
        'click .btn-danger': 'onCloseButtonClick',
        'click .btn-success': 'onSendMessageClick',
    },
    init() {
        this._super.apply(this, arguments);
        this.rpc = this.bindService("rpc");
    },
    // Hide the message templates if selected value is 'Custom'
    onclickCustomRadio: function () {
        document.querySelector('#myFormControl').style.display = "none";
    },
    // Show the message templates if selected value is 'Default'
    onclickDefaultRadio: function () {
        document.querySelector('#myFormControl').style.display = "block";
        let data = jsonrpc('/whatsapp_message', {data:'data'})
        this.updateUI(data);
    },
    // Updates the user interface with message templates.
    updateUI: function (data) {
        var selectElement = document.querySelector("#myFormControl");
        selectElement.innerHTML = '';               // Clear existing options
        var defaultOption = document.createElement('option');
        defaultOption.textContent = 'Select the Template';
        selectElement.appendChild(defaultOption);   // Add default option
        // Add options from the data
        data.then((result) => {
            const messages = result.messages;
            messages.forEach((message) => {
                var option = document.createElement('option');
                option.value = message.id;
                option.textContent = message.name;
                option.setAttribute('data-message', message.message);  // Save the message as a data attribute
                selectElement.appendChild(option);
            });
        })
    },
    // Updates the selected message templates
    onSelectChange: function () {
        var selectElement = document.querySelector("#myFormControl");
        var textareaElement = document.querySelector("#exampleFormControlTextarea1");
        var selectedOption = selectElement.options[selectElement.selectedIndex];
        var selectedMessage = selectedOption.getAttribute('data-message');
        textareaElement.value = selectedMessage;    // Update the textarea with the message from the selected option
    },
    //Closing the Modal
    onCloseButtonClick: function () {
        document.querySelector("#ModalWhatsapp").style.display = "none";
    },
    // Send Message to Whatsapp
    onSendMessageClick: function () {
        var textareaElement = document.querySelector("#exampleFormControlTextarea1");
        var messageString = textareaElement.value;
        let data = jsonrpc('/mobile_number', {data:'data'})
        data.then((result) => {
            const mobile_num = result.mobile;
            mobile_num.forEach((mobile) => {
                // Check if 'mobile_number' is present in the first item of the 'data' array and is not falsy
                if (mobile_num && mobile_num.length > 0 && 'mobile_number' in mobile_num[0] && mobile_num[0].mobile_number) {
                    var mobileNumber = mobile_num[0].mobile_number;
                    // Construct the WhatsApp URL using the mobile number and messageString
                    var whatsappUrl = 'https://api.whatsapp.com/send?phone=' + mobileNumber + '&text=' + encodeURIComponent(messageString);
                    // Open the WhatsApp URL in a new tab or window
                    window.open(whatsappUrl, '_blank');
                } else {
                    // If mobile number is not available or falsy, You might want to display a user-friendly error message on the UI"
                    document.querySelector("#phoneMessage").style.display = "block";
                }
            });
        })
    },
});
export default publicWidget.registry.deliveryDateToggl;
