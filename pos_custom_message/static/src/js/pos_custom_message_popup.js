/** @odoo-module */
import ProductScreen from 'point_of_sale.ProductScreen';
import Registries from 'point_of_sale.Registries';
/**
 * PosCustomMessage extends the ProductScreen class to display custom message popups at specific execution times.
 * Inherits from ProductScreen.
 */
const PosCustomMessage = ProductScreen =>
    class extends ProductScreen {
        setup() {
            super.setup();
            var self = this;
            setInterval(function() {
                const messages = self.env.pos.pos_custom_message;
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
                                //Alert message popup
                                self.showPopup('CustomMessageAlertPopup', {
                                    title: msg.title,
                                    body: msg.message_text,
                                });
                            if (msg.message_type == "warn")
                                // Warning message popup
                                self.showPopup('CustomMessageWarnPopup', {
                                    title: msg.title,
                                    body: msg.message_text,
                                });
                            if (msg.message_type == "info")
                                // Information message popup
                                self.showPopup('CustomMessageInfoPopup', {
                                    title: msg.title,
                                    body: msg.message_text,
                                });
                        }
                    });
                }
            }, 1000);
        }
    }
Registries.Component.extend(ProductScreen, PosCustomMessage);