/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
//  Define a new class named 'WhatsappIcon' that extends the 'publicWidget.Widget' class
publicWidget.registry.WhatsappIcon = publicWidget.Widget.extend({
    selector: '.cy_whatsapp_web',
    events: {
        'click': '_onClickWhatsappIcon',
    },
    start: function() {
        this._super.apply(this, arguments);
    },
    // Displays selection messages while clicking on whatsapp icon
    _onClickWhatsappIcon: function (ev) {
        $('#ModalWhatsapp').css('display', 'block');
    },
});
export default publicWidget.registry.WhatsappIcon;
