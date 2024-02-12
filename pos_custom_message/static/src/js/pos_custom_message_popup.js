/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { CustomMessageAlertPopup } from "@pos_custom_message/js/Popup/AlertPopup";
import { CustomMessageInfoPopup } from "@pos_custom_message/js/Popup/InfoPopup";
import { CustomMessageWarnPopup } from "@pos_custom_message/js/Popup/WarningPopup";


// Patching the ProductScreen to add Section function
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        var self = this;
        setInterval(function () {
            const messages = self.env.services.pos.pos_custom_message
            if (messages) {
                messages.forEach((msg) => {
                    const exec_time = msg.execution_time;
                    const hours = Math.floor(exec_time);
                    const minutes = Math.round((exec_time % 1) * 60);
                    const ExecutionTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
                    const now = new Date();
                    const now_hours = now.getHours();
                    const now_minutes = now.getMinutes();
                    const now_seconds = now.getSeconds();
                    const formattedTimeNow = `${now_hours.toString().padStart(2, '0')}:${now_minutes.toString().padStart(2, '0')}:${now_seconds.toString().padStart(2, '0')}`;
                    if (ExecutionTime === formattedTimeNow) {
                        if (msg.message_type == "alert")
                            // Alert message popup
                            self.popup.add(CustomMessageAlertPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                        if (msg.message_type == "warn")
                            // Warning message popup
                            self.popup.add(CustomMessageWarnPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                        if (msg.message_type == "info")
                            // Information message popup
                            self.popup.add(CustomMessageInfoPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                    }
                });
            }
        }, 1000);
    },
});
