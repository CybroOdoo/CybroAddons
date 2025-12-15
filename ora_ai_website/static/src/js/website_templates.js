/** @odoo-module **/
import { rpc } from "@web/core/network/rpc";
import { Interaction } from '@web/public/interaction';
import { patchDynamicContent } from '@web/public/utils';
import { WebsiteSale } from '@website_sale/interactions/website_sale';
import { patch } from '@web/core/utils/patch';

patch(WebsiteSale.prototype, {
    async setup(services) {
        super.setup();
        patchDynamicContent(this.dynamicContent, {
            '.website_assistant_container': {
                't-on-click': this.onClick.bind(this),
            },
        });
        this.isAssistantActive = false;
        this.microElement = document.querySelector('.micro');
        await this._fetchProductName();
        const data = await this._fetchAssistantData();
        window.apiKey = data.public_api_key;
        window.assistant = data.assistant;
        this._loadVapiScript();
    },

    async _fetchProductName() {
        const result = await rpc('/get_product_name', {});
        this.product_name = result.product_name;
    },

    async _fetchAssistantData() {
        const response = await rpc('/website_assistant', {});
        this.data = response;
        return response;
    },

    _loadVapiScript() {
        (function (d, t) {
            const g = document.createElement(t),
                  s = d.getElementsByTagName(t)[0];
            g.src = "/ora_ai_base/static/src/lib/vapi.min.js";
            g.defer = true;
            g.async = true;
            s.parentNode.insertBefore(g, s);
        })(document, "script");
    },

     onClick() {
        if (this.isAssistantActive) {
            this.stop_assistant();
        } else {
            this.start_assistant();
            this.microElement.classList.add('active');
        }
     },

     stop_assistant() {
        this.VAPI.stop()
     },

     async start_assistant() {
        this.isAssistantActive = !this.isAssistantActive;
        const VAPI = window.vapiSDK.run({
            apiKey: this.data.public_api_key,
            assistant: this.data.assistant,
        });
        this.VAPI = VAPI;
        VAPI.start(window.assistant);
        if (VAPI) {
            VAPI.on("message", async (message) => {
                if (message.type === "tool-calls") {
                    if (message.toolCallList[0].function.arguments.LanguagePreference){
                        await this.update_assistant(message.toolCallList[0].function.arguments.LanguagePreference.LanguageCode, this.data.assistant)
                    }
                    if (message.toolCallList[0].function.arguments.OrderDetails){
                         await this._handleToolCalls(message.toolCallList[0].function.arguments.OrderDetails.Products);
                    }
                }
                if (message.transcriptType === "final" && message.role === "assistant") {
                    const assistant_msg = message.transcript.toLowerCase();
                    this.highlight_product_card_transcriber(assistant_msg);
                }
            });
            VAPI.on("call-end", () => {
                this.isAssistantActive = false;
                if (this.is_lang_set){
                   this.reset_assistant()
                }
                this.el.querySelectorAll('div.oe_product').forEach((el) => {
                 $(this).css({
                     'box-shadow': 'none'
                   });
              })
            });
            VAPI.on('speech-start', () => {
                this.microElement.classList.add('speech-active');
            });
            VAPI.on('speech-end', () => {
                this.microElement.classList.remove('speech-active');
            });
            VAPI.on('call-end', () => {
                this.microElement.classList.remove('speech-active');
                this.microElement.classList.remove('active');
            });
        }
    },

    async reset_assistant() {
       const response = await rpc(`/web/dataset/call_kw/vapi.voice.assistant/reset_assistant`, {
         model: "vapi.voice.assistant",
         method: "reset_assistant",
         args: [],
         kwargs: {'assistant_id': this.data.assistant},
       });
    },

    async update_assistant(LanguageCode, assistant_id) {
         const lang_obj = await rpc(`/web/dataset/call_kw/vapi.language/get_language`, {
             model: "vapi.language",
             method: "get_language",
             args: [],
             kwargs: {'language': LanguageCode},
         });
         if (lang_obj.status) {
            this.is_lang_seproductst = false
            this.VAPI.stop()
            const options = {
              method: 'PATCH',
              headers: {
                Authorization: `Bearer ${this.data.private_api_key}`,
                'Content-Type': 'application/json'
              },
              body: `{
                  "transcriber":{
                      "language": "${LanguageCode}",
                      "provider":"deepgram",
                      "model":"nova-2"
                  },
                  "voice":{
                       "provider":"11labs",
                       "voiceId":"${lang_obj.voice}"
                  },
                  "firstMessage":"${lang_obj.first_msg}",
                  "endCallPhrases":["${lang_obj.end_msg}"]
              }`
            };
            const response = await fetch(`https://api.vapi.ai/assistant/${this.data.assistant}`, options)
            if (response.ok) {
                this.is_lang_set = true
                this.start_assistant()
            }
         }
    },

    async _handleToolCalls(products) {
        const data = await rpc("/shop/add_cart_order", {});
        if (data?.is_order) {
            products.forEach(async item => {
                if (item.productId && item.Quantity) {
                    const productTempId = await rpc("/get_product_template_id", { product:item.productId })
                    await this.services['cart'].add({
                        productTemplateId: productTempId,
                        productId: item.productId,
                        quantity: item.Quantity,
                    });
                }
            })
        }
        this.el.querySelectorAll('div.oe_product').forEach((el) => {
             $(this).css({
                 'box-shadow': 'none'
             });
        })
        setTimeout(() => this.stop_assistant(), 15000);
    },

    async highlight_product_card_transcriber(assistant_msg) {
        let matchedProduct = null;
        for (let i = 0; i < this.product_name.length; i++) {
            if (assistant_msg.replace(/block/g, 'bloc').includes(this.product_name[i].toLowerCase())) {
                matchedProduct = this.product_name[i];
                break;
            }
        }
        if (matchedProduct) {
            this.el.querySelectorAll('div.oe_product').forEach((card) => {
                const span = card.querySelector('h2.o_wsale_products_item_title span');
                const productText = span ? span.textContent.trim() : "";

                if (productText === matchedProduct) {
                    card.querySelector('form').style.boxShadow = "0px 22px 70px 4px rgba(0, 0, 0, 0.56)";
                } else {
                   card.querySelector('form').style.boxShadow = "none";
                }
            });
        }

    },
})