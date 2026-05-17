import { Discuss } from "@mail/core/public_web/discuss";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { onMounted } from "@odoo/owl";

patch(Discuss.prototype, {
    setup() {
        super.setup(...arguments);

        onMounted(async () => {
            await new Promise(resolve => setTimeout(resolve, 200));

            try {
                const result = await rpc('/select_color', {});

                // Create or get style element
                let styleEl = document.getElementById('discuss-custom-bg');
                if (!styleEl) {
                    styleEl = document.createElement('style');
                    styleEl.id = 'discuss-custom-bg';
                    document.head.appendChild(styleEl);
                }

                let cssRules = '';

                // PRIORITY: If image exists, use image. Otherwise use color.
                if (result.background_image) {
                    // Image takes priority - no background color
                    cssRules += `
                        .o-mail-Discuss,
                        .o-mail-Discuss-content,
                        .o-mail-Thread,
                        .o-mail-Thread-messageList,
                        .o_mail_Discuss_content {
                            background-image: url(data:image/png;base64,${result.background_image}) !important;
                            background-size: cover !important;
                            background-position: center !important;
                            background-repeat: no-repeat !important;
                            background-attachment: fixed !important;
                            background-color: transparent !important;
                        }
                    `;
                } else if (result.background_color) {
                    // Only apply color if no image
                    cssRules += `
                        .o-mail-Discuss,
                        .o-mail-Discuss-content,
                        .o-mail-Thread,
                        .o-mail-Thread-messageList,
                        .o_mail_Discuss_content {
                            background-color: ${result.background_color} !important;
                            background-image: none !important;
                        }
                    `;
                }

                if (result.layout_color) {
                    cssRules += `
                        :root {
                            --layout-color: ${result.layout_color} !important;
                        }
                    `;
                }

                // Optional: Make messages more readable when image is present
                if (result.background_image) {
                    cssRules += `
                        .o-mail-Message {
                            background-color: rgba(255, 255, 255, 0.5) !important;
                            backdrop-filter: blur(10px);
                            border-radius: 10px !important;
                            margin-bottom: 8px !important;
                        }
                    `;
                }

                styleEl.textContent = cssRules;

            } catch (error) {
                console.error("✗ Error:", error);
            }
        });
    },
});