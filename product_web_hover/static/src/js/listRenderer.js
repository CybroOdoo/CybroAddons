odoo.define('product_web_hover.ListRenderer', function (require) {
    "use strict";

    var ListRenderer = require('web.ListRenderer');

    ListRenderer.include({
        _renderBodyCell: function (record, node, colIndex, options) {
            var result = this._super.apply(this, arguments);

            if (typeof record.data[node.attrs.name] === "object" && record.data[node.attrs.name].model === "product.product") {
                this.getProductFromBackend(record.data[node.attrs.name].data?.id)
                    .then(productInfo => {
                        result.attr('data-tooltip-info', JSON.stringify(productInfo))
                              .attr('data-tooltip-template', "product_web_hover.HoverTemplate");
                    })
            }

            return result;
        },

        getProductFromBackend: async function(productId) {
            if (productId) {
                const requiredData = await this._rpc({
                        model: "product.product",
                        method: "read",
                        args: [[productId], []],
                });

                if (requiredData && requiredData.length > 0) {
                        return {
                            name: requiredData[0].name,
                            categ_id: requiredData[0].categ_id[1],
                            code: requiredData[0].code,
                            list_price: requiredData[0].list_price,
                            standard_price: requiredData[0].standard_price,
                            qty_available: requiredData[0].qty_available,
                            image_1920: requiredData[0].image_1920
                        };
                }
            }
        }
    });
});
