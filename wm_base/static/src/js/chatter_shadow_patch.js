/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { Message } from "@mail/core/common/message";
import { useEffect } from "@odoo/owl";

patch(Message.prototype, {
    setup() {
        super.setup(...arguments);
        useEffect(
            () => {
                if (this.shadowRoot) {
                    const shadowFixStyle = document.createElement("style");
                    shadowFixStyle.textContent = `
                        * {
                            color: #1F2937 !important;
                            background-color: transparent !important;
                        }
                        a, a * {
                            color: #1976D2 !important;
                        }
                    `;
                    this.shadowRoot.appendChild(shadowFixStyle);
                }
            },
            () => [this.shadowRoot, this.props.message?.body, this.props.message?.richBody]
        );
    }
});
