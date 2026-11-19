import { registry } from "@web/core/registry";

/**
 * Fake Vapi SDK: the test sends the messages of the call
 */
function installFakeVapi() {
    const vapi = {
        handlers: {},
        starts: [],
        on(event, callback) {
            (this.handlers[event] ||= []).push(callback);
        },
        emit(event, payload) {
            for (const callback of this.handlers[event] || []) {
                callback(payload);
            }
        },
        start(assistant, overrides) {
            this.starts.push({ assistant, overrides });
            // Lets the steps wait for the call
            document.body.dataset.oraCallLanguage = overrides?.transcriber?.language || "default";
            this.emit("call-start");
        },
        stop() {
            this.emit("call-end");
        },
    };
    window.vapiSDK = { run: () => vapi };
    window.oraFakeVapi = vapi;
}

function toolCall(args) {
    return { type: "tool-calls", toolCallList: [{ function: { arguments: args } }] };
}

registry.category("web_tour.tours").add("ora_ai_website_voice_order", {
    steps: () => [
        {
            content: "Install the fake Vapi SDK",
            trigger: ".o_ora_website_assistant:contains(Burger Bot)",
            run: installFakeVapi,
        },
        {
            content: "Start the call",
            trigger: ".o_ora_website_assistant",
            run: "click",
        },
        {
            content: "The call started with the default language",
            trigger: "body[data-ora-call-language=default] .o_ora_micro.active",
            run() {
                const start = window.oraFakeVapi.starts[0];
                if (start.assistant !== "asst-1" || start.overrides) {
                    throw new Error(`Wrong start: ${JSON.stringify(start)}`);
                }
                window.oraFakeVapi.emit(
                    "message",
                    toolCall({ LanguagePreference: { LanguageCode: "fr" } })
                );
            },
        },
        {
            content: "The call starts again in French",
            trigger: "body[data-ora-call-language=fr] .o_ora_micro.active",
            run() {
                const start = window.oraFakeVapi.starts[1];
                if (start?.overrides?.transcriber?.language !== "fr") {
                    throw new Error(`No French restart: ${JSON.stringify(start)}`);
                }
                window.oraFakeVapi.emit("message", {
                    type: "transcript",
                    transcriptType: "final",
                    role: "assistant",
                    transcript: "Our ora burger costs 12.50",
                });
            },
        },
        {
            content: "The product the assistant talks about is highlighted",
            trigger: ".oe_product.o_ora_highlight:contains(Ora Burger)",
            run() {
                const productId = new URLSearchParams(location.hash.slice(1)).get("product");
                window.oraFakeVapi.emit(
                    "message",
                    toolCall({
                        OrderDetails: {
                            Products: [
                                { Product: "Ora Burger", productId, Quantity: 2 },
                                { Product: "Made up", productId: 999999999, Quantity: 1 },
                            ],
                        },
                    })
                );
            },
        },
        {
            content: "The ordered product is in the cart",
            trigger: ".my_cart_quantity:contains(2)",
        },
        {
            content: "No highlight after the order",
            trigger: ".o_wsale_products_page:not(:has(.o_ora_highlight))",
            run() {
                window.oraFakeVapi.emit("speech-start");
            },
        },
        {
            content: "The button shows when the assistant speaks",
            trigger: ".o_ora_micro.speech-active",
            run() {
                window.oraFakeVapi.stop();
            },
        },
        {
            content: "The call ended",
            trigger: ".o_ora_website_assistant:not(:has(.o_ora_micro.active))",
        },
    ],
});
