/** @odoo-module */
import {
    FormArchParser
} from "@web/views/form/form_arch_parser";
import {
    patch
} from "@web/core/utils/patch";
import {
    archParseBoolean
} from "@web/views/utils";
var rpc = require('web.rpc');

patch(FormArchParser.prototype, "parse", {
    /**
     * Patched version of the 'parse' method in 'FormArchParser'.
     * Modifies the parsing behavior by removing the chatter node from the XML if the model is configured to hide the chatter.
     *
     * @param {string} arch - The XML architecture to parse.
     * @param {Object} models - The model definitions.
     * @param {string} modelName - The name of the model being parsed.
     * @returns {Object} - The parsed result.
     */
    parse(arch, models, modelName) {
        const parsedResult = this._super.apply(this, arguments);
        rpc.query({
            model: "ir.model",
            method: "search",
            args: [
                [
                    ["model", "=", modelName]
                ]
            ],
            kwargs: {
                limit: 1
            },
        }).then((result) => {
            const resModelId = result;
            rpc.query({
                model: "ir.config_parameter",
                method: "get_param",
                args: ["chatter_enable.model_ids"],
            }).then((result) => {
                const modelIds = JSON.parse(result);
                if (modelIds){
                    if (modelIds.includes(resModelId[0])) {
                        const {
                            xmlDoc
                        } = parsedResult;
                        const chatterNode = xmlDoc.querySelector("div.oe_chatter");
                        if (chatterNode && chatterNode.parentElement) {
                            chatterNode.parentElement.removeChild(chatterNode);
                        }
                    }
                }
            })
        })
        return parsedResult;
    },
});
