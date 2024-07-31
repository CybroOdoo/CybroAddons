odoo.define('pos_custom_message.PosCustomMessage', function (require) {
    'use strict';

    const ProductScreen = require('point_of_sale.ProductScreen');
    const _super_ProductScreen = ProductScreen.prototype;
    const Registries = require('point_of_sale.Registries');

    const PosCustomMessage = (ProductScreen) =>
        class extends ProductScreen {
            constructor() {
                super(...arguments);
                var self = this;
                setInterval(function() {
                    const messages = self.env.pos.pos_custom_message;
                    if (messages) {
                        for (let msg in messages) {
                            const exec_time = messages[msg].execution_time;
                            const hours = Math.floor(exec_time);
                            const minutes = Math.round((exec_time % 1) * 60);
                            const ExecutionTime = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
                            const now = new Date();
                            const now_hours = now.getHours();
                            const now_minutes = now.getMinutes();
                            const now_seconds = now.getSeconds();
                            const formattedTimeNow = `${now_hours.toString().padStart(2, '0')}:${now_minutes.toString().padStart(2, '0')}:${now_seconds.toString().padStart(2, '0')}`;
                            if (ExecutionTime === formattedTimeNow) {
                                if (messages[msg].message_type == "alert") {
                                    //Alert message popup
                                    self.showPopup('CustomMessageAlertPopup', {
                                        title: messages[msg].title,
                                        body: messages[msg].message_text,
                                    });
                                }
                                if (messages[msg].message_type == "warn") {
                                    // Warning message popup
                                    self.showPopup('CustomMessageWarnPopup', {
                                        title: messages[msg].title,
                                        body: messages[msg].message_text,
                                    });
                                }
                                if (messages[msg].message_type == "info") {
                                    // Information message popup
                                    self.showPopup('CustomMessageInfoPopup', {
                                        title: messages[msg].title,
                                        body: messages[msg].message_text,
                                    });
                                }
                            }
                        };
                    }
                }, 1000);
            }
        };

    Registries.Component.extend(ProductScreen, PosCustomMessage);

    return ProductScreen;
});
