/**
 * WhatsApp Chat Layout - Discuss Container Theming for Odoo 20
 * Applies the configured background color, background image, and layout color
 * to the Discuss conversation pane and components.
 */
import { Discuss } from "@mail/core/public_web/discuss_app/discuss_app";
import { patch } from "@web/core/utils/patch";
import { rpc } from "@web/core/network/rpc";
import { onMounted } from "@odoo/owl";

export async function applyDiscussTheme() {
    try {
        const result = await rpc("/select_color", {});
        if (!result) {
            return;
        }

        let styleEl = document.getElementById("discuss-custom-bg");
        if (!styleEl) {
            styleEl = document.createElement("style");
            styleEl.id = "discuss-custom-bg";
            document.head.appendChild(styleEl);
        }

        const layoutColor = result.layout_color || "#00a884";
        const bgColor = result.background_color || "#ECE5DD";
        const hasImage = !!(
            result.background_image &&
            typeof result.background_image === "string" &&
            !result.background_image.startsWith("BinaryValue") &&
            result.background_image.length > 20
        );

        let mime = "image/png";
        if (hasImage) {
            if (result.background_image.startsWith("/9j/")) {
                mime = "image/jpeg";
            } else if (result.background_image.startsWith("R0lGOD")) {
                mime = "image/gif";
            } else if (result.background_image.startsWith("UklGR")) {
                mime = "image/webp";
            } else if (result.background_image.startsWith("PHN2Zy") || result.background_image.startsWith("PD94bW")) {
                mime = "image/svg+xml";
            }
        }

        const bgImageVal = hasImage
            ? `url("data:${mime};base64,${result.background_image}")`
            : "none";

        // Set CSS custom properties on document root
        const root = document.documentElement;
        root.style.setProperty("--layout-color", layoutColor);
        root.style.setProperty("--background-color", bgColor);
        if (hasImage) {
            root.style.setProperty("--background-image", bgImageVal);
        } else {
            root.style.removeProperty("--background-image");
        }

        let cssRules = `
            :root {
                --layout-color: ${layoutColor} !important;
                --background-color: ${bgColor} !important;
            }

            /* Main Discuss container: hosts the background color and wallpaper */
            .o-mail-Discuss {
                background-color: ${bgColor} !important;
                background-image: ${bgImageVal} !important;
                background-size: cover !important;
                background-position: center !important;
                background-repeat: no-repeat !important;
            }

            /* Keep the WhatsApp left sidebar solid white */
            .o-mail-DiscussApp-sidebar,
            .o-mail-DiscussApp-sidebar .o-mail-MessagingMenu {
                background-color: #ffffff !important;
                background-image: none !important;
            }

            /* Chat header pill (contact / channel info) */
            .o-mail-DiscussContent-headerBox {
                background-color: #ffffff !important;
                background-image: none !important;
                box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
            }

            /* Members panel on the right */
            .o-mail-DiscussContent-panelContainer {
                background-color: #ffffff !important;
                background-image: none !important;
            }

            /* Composer at bottom */
            .o_Composer,
            .o-mail-Composer {
                background-color: #ffffff !important;
                background-image: none !important;
            }

            /* Make DiscussContent and all intermediate chat containers transparent
               so the background image and color on .o-mail-Discuss shine through cleanly! */
            .o-mail-DiscussContent,
            .o-mail-DiscussContent-main,
            .o-mail-DiscussContent-core,
            .o-mail-DiscussContent-core > div,
            .o-mail-DiscussContent-core .bg-inherit,
            .o-mail-DiscussContent .bg-inherit,
            .o-mail-Thread,
            .o-mail-Thread-content,
            .o-mail-Thread-empty {
                background-color: transparent !important;
                background: transparent !important;
                background-image: none !important;
            }

            /* WhatsApp Layout Color styling for active elements */
            .wa-tab-btn.wa-tab-active {
                color: ${layoutColor} !important;
                border-bottom: 3px solid ${layoutColor} !important;
            }

            .wa-tab-btn:hover {
                color: ${layoutColor} !important;
            }

            .o-mail-DiscussSidebarCategory {
                height: 74px;
                background-color: ${layoutColor} !important;
            }

            .o-mail-DiscussSidebarCategory span,
            .o-mail-DiscussSidebarCategory-icon,
            .o-mail-DiscussSidebarCategory-add,
            i.o_DiscussSidebarCategory_command {
                color: #ffffff !important;
            }

            .o-mail-ThreadIcon {
                color: ${layoutColor} !important;
            }

            button.o-mail-Composer-send {
                background-color: ${layoutColor} !important;
                color: #ffffff !important;
            }
        `;

        if (hasImage) {
            cssRules += `
                .o-mail-Thread-startMessage {
                    background-color: rgba(255, 255, 255, 0.88) !important;
                    backdrop-filter: blur(8px);
                    border-radius: 12px !important;
                    padding: 16px 20px !important;
                    margin: 12px 0 !important;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
                }

                .o-mail-DateSection-date {
                    background-color: rgba(255, 255, 255, 0.85) !important;
                    border-radius: 8px !important;
                    padding: 3px 12px !important;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08) !important;
                }

                .o-mail-Message {
                    background-color: rgba(255, 255, 255, 0.92) !important;
                    backdrop-filter: blur(8px);
                    border-radius: 10px !important;
                    margin-bottom: 8px !important;
                    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
                }
            `;
        }

        styleEl.textContent = cssRules;
    } catch (error) {
        console.error("Failed to apply discuss theme:", error);
    }
}

patch(Discuss.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(() => {
            applyDiscussTheme();
        });
    },
});
