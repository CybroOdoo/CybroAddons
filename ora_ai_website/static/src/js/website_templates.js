import { loadJS } from "@web/core/assets";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";

const VAPI_SDK = "/ora_ai_base/static/src/lib/vapi.min.js";
// Time left to the visitor to hear the order summary before the call ends
const END_CALL_DELAY = 15000;

/**
 * Talk with the voice assistant from the shop page: the products the
 * assistant talks about are highlighted, and the ordered products are added
 * to the cart.
 */
export class OraWebsiteAssistant extends Interaction {
    static selector = ".o_ora_website_assistant";
    dynamicContent = {
        _root: { "t-on-click": this.onClick },
        ".o_ora_micro": {
            "t-att-class": () => ({
                active: this.inCall,
                "speech-active": this.speaking,
            }),
        },
    };

    setup() {
        this.data = {};
        this.vapi = null;
        this.inCall = false;
        this.speaking = false;
        // Settings of the call in the language chosen by the visitor
        this.overrides = undefined;
        this.restarting = false;
    }

    async willStart() {
        this.data = await this.waitFor(rpc("/ora_ai_website/assistant"));
        if (this.data.assistant) {
            await this.waitFor(loadJS(VAPI_SDK));
        }
        this.registerCleanup(() => {
            this.vapi?.stop();
            this.highlightProduct(null);
        });
    }

    onClick() {
        if (!this.data.assistant || !window.vapiSDK) {
            return;
        }
        if (this.inCall) {
            this.vapi.stop();
            return;
        }
        if (!this.vapi) {
            this.vapi = window.vapiSDK.run({
                apiKey: this.data.public_api_key,
                assistant: this.data.assistant,
            });
            this.onVapi("call-start", () => (this.inCall = true));
            this.onVapi("call-end", () => this.onCallEnd());
            this.onVapi("speech-start", () => (this.speaking = true));
            this.onVapi("speech-end", () => (this.speaking = false));
            this.onVapi("message", (message) => this.onMessage(message));
            this.onVapi("error", () => {
                this.inCall = this.speaking = false;
            });
        }
        this.inCall = true;
        this.vapi.start(this.data.assistant, this.overrides);
    }

    /**
     * Listen to the events of the call, and update the button after them
     */
    onVapi(event, callback) {
        this.vapi.on(event, (...args) => {
            if (!this.isDestroyed) {
                callback(...args);
                this.updateContent();
            }
        });
    }

    onCallEnd() {
        this.inCall = this.speaking = false;
        if (this.restarting) {
            // Start again in the language chosen by the visitor
            this.restarting = false;
            this.inCall = true;
            this.vapi.start(this.data.assistant, this.overrides);
            return;
        }
        // The next call starts in the default language again
        this.overrides = undefined;
        this.highlightProduct(null);
    }

    async onMessage(message) {
        if (message.type === "tool-calls") {
            const args = message.toolCallList?.[0]?.function?.arguments || {};
            if (args.LanguagePreference?.LanguageCode) {
                await this.switchLanguage(args.LanguagePreference.LanguageCode);
            }
            if (args.OrderDetails?.Products) {
                await this.addToCart(args.OrderDetails.Products);
            }
        } else if (
            message.type === "transcript" &&
            message.transcriptType === "final" &&
            message.role === "assistant"
        ) {
            const productName = this.findProduct(message.transcript);
            if (productName) {
                this.highlightProduct(productName);
            }
        }
    }

    async switchLanguage(code) {
        const overrides = await this.waitFor(rpc("/ora_ai_website/language", { code }));
        if (Object.keys(overrides).length) {
            this.overrides = overrides;
            this.restarting = true;
            this.vapi.stop();
        }
    }

    async addToCart(products) {
        const templates = await this.waitFor(
            rpc("/ora_ai_website/products", {
                product_ids: products.map((item) => item.productId),
            })
        );
        // One by one, so that the products go in the same cart
        for (const item of products) {
            const productTemplateId = templates[item.productId];
            if (productTemplateId && item.Quantity > 0) {
                await this.waitFor(
                    this.services.cart.add({
                        productTemplateId,
                        productId: Number(item.productId),
                        quantity: item.Quantity,
                    })
                );
            }
        }
        this.highlightProduct(null);
        this.waitForTimeout(() => this.vapi?.stop(), END_CALL_DELAY);
    }

    /**
     * Name of the longest published product the assistant talks about
     */
    findProduct(transcript) {
        const text = transcript.toLowerCase();
        return (this.data.product_names || [])
            .filter((name) => text.includes(name.toLowerCase()))
            .sort((a, b) => b.length - a.length)[0];
    }

    /**
     * Highlight the card of the product, or none without a name
     */
    highlightProduct(productName) {
        for (const card of document.querySelectorAll(".o_wsale_products_page .oe_product")) {
            const title = card.querySelector(".o_wsale_products_item_title a > span");
            card.classList.toggle(
                "o_ora_highlight",
                !!productName && title?.textContent.trim() === productName
            );
        }
    }
}

registry.category("public.interactions").add("ora_ai_website.assistant", OraWebsiteAssistant);
