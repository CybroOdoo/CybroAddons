/** @odoo-module */
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { AlertPopup } from "@pos_custom_message/app/utils/alert_popup/alert_popup";
import { InfoPopup } from "@pos_custom_message/app/utils/info_popup/info_popup";
import { WarningPopup } from "@pos_custom_message/app/utils/warning_popup/warning_popup";



// Patching the ProductScreen to add Section function
patch(ProductScreen.prototype, {
    setup() {
        super.setup();
        var self = this;
        setInterval(function () {
            const messages = self.pos.config.message_ids
            if (messages.length) {
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
                         if (msg.message_type == "alert"){
                            self.dialog.add(AlertPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                         }
                         if (msg.message_type == "warn") {
                            self.dialog.add(WarningPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                        }
                        if (msg.message_type == "info") {
                            self.dialog.add(InfoPopup, {
                                title: msg.title,
                                body: msg.message_text,
                            });
                        }
                    }
                })
            }
        }, 1000);
    },
});
