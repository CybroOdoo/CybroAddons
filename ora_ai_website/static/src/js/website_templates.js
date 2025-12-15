/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import wSaleUtils from "@website_sale/js/website_sale_utils";

// Public widget integrates a voice assistant into the website shop interface.
publicWidget.registry.VoiceAssistantButton = publicWidget.Widget.extend({
    selector: '.oe_website_sale',
    events: {
        'click .website_assistant_container': '_onClick',
    },
    init() {
        this._super(...arguments);
        this.rpc = rpc;
        this.isAssistantActive = false;
        this.microElement = document.querySelector('.micro');
    },
    start: async function () {
        await this._fetchProductName();
        const data = await this._fetchAssistantData();
        window.apiKey = data.public_api_key;
        window.assistant = data.assistant;
        this._loadVapiScript();
    },
    _fetchProductName: async function () {
        const result = await this.rpc('/get_product_name', {});
        this.product_name = result.product_name;
    },
    _fetchAssistantData: async function () {
        const response = await this.rpc('/website_assistant', {});
        this.data = response;
        return response;
    },
    _loadVapiScript: function () {
        (function (d, t) {
            const g = document.createElement(t),
                  s = d.getElementsByTagName(t)[0];
            g.src = "/ora_ai_base/static/src/lib/vapi.min.js";
            g.defer = true;
            g.async = true;
            s.parentNode.insertBefore(g, s);
        })(document, "script");
    },
    _onClick: function () {
        if (this.isAssistantActive) {
            this.stop_assistant();
        } else {
            this.start_assistant();
            this.microElement.classList.add('active');
        }
    },
    stop_assistant: function() {
       this.VAPI.stop()
    },
    start_assistant: async function() {
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
                this.$el.find('td.oe_product').each(function () {
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
    reset_assistant: async function() {
       const response = await this.rpc(`/web/dataset/call_kw/vapi.voice.assistant/reset_assistant`, {
         model: "vapi.voice.assistant",
         method: "reset_assistant",
         args: [],
         kwargs: {'assistant_id': this.data.assistant},
       });
    },
    update_assistant: async function(LanguageCode, assistant_id) {
         const lang_obj = await this.rpc(`/web/dataset/call_kw/vapi.language/get_language`, {
             model: "vapi.language",
             method: "get_language",
             args: [],
             kwargs: {'language': LanguageCode},
         });
         if (lang_obj.status) {
            this.is_lang_set = false
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
    _handleToolCalls: async function (products) {
        const productQtyDict = {};
        await Promise.all(products.map(async (item) => {
            if (item.productId && item.Quantity) {
                productQtyDict[item.productId] = item.Quantity;
            }
        }));
        await this.rpc("/shop/add_to_cart", { products: productQtyDict
        }).then((data) => {
              data.values.map(async (item) => {
                 wSaleUtils.updateCartNavBar(item);
                 wSaleUtils.showCartNotification(this.call.bind(this), item.notification_info);
              })
              this.$el.find('td.oe_product').each(function () {
                 $(this).css({
                     'box-shadow': 'none'
                   });
              })
              setTimeout(() => this.stop_assistant(), 15000);
        });
    },
    highlight_product_card_transcriber: async function(assistant_msg) {
        let matchedProduct = null;
        for (let i = 0; i < this.product_name.length; i++) {
            if (assistant_msg.replace(/block/g, 'bloc').includes(this.product_name[i].toLowerCase())) {
                matchedProduct = this.product_name[i];
                break;
            }
        }
        if (matchedProduct) {
            this.$el.find('div.oe_product').each(function () {
                const productText = $(this).find('h6.o_wsale_products_item_title').text().trim();
                if (productText === matchedProduct) {
                    $(this).css({
                        'box-shadow': 'rgba(0, 0, 0, 0.56) 0px 22px 70px 4px'
                    });
                }
                else {
                   $(this).css({
                     'box-shadow': 'none'
                   });
                }
            });
        }
    },
});