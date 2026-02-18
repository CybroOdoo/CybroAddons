//** @odoo-module */
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";
patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService('orm');
        this.state = useState({

            qty_available: 0,
            incoming_qty: 0,
            outgoing_qty: 0,

            // ADD THESE
            on_hand_loc: 0,
            incoming_loc: 0,
            outgoing_loc: 0,
            display_stock: false,
        });
    },

    async fetchProductDetails(productId) {
        const product = await this.orm.call("product.template", "read", [[productId], ["name", "id", "incoming_qty","outgoing_qty","qty_available", "location_id"]]);
        return product[0];
    },

    async _loadLocationStock(productId) {
        const locationId = this.pos.config.pos_stock_location_id;
        if (!locationId) return;

        const quants = await this.orm.call(
            "stock.quant",
            "search_read",
            [[["product_tmpl_id", "=", productId],["location_id", "=", locationId]],["quantity", "available_quantity", "product_id","product_tmpl_id" ,"location_id"]]);

        this.location_stock_quant = quants.reduce(
            (total, q) => total + (q.available_quantity || 0),
            0
        );
    },

    async after_load_server_data() {
        await super.after_load_server_data(...arguments);
        await this._loadLocationStock();
    },


    async updateProductDetails() {
        const productId = this.props.productId;
        const locationId = this.pos.config.pos_stock_location_id;
        if (productId) {
            this.productDetail = await this.fetchProductDetails(productId);
            const product_product = this.pos.product_product;
            const stock_product = this.pos.stock_quant;
            const main_product = product_product.find(product => product.product_tmpl_id.id === productId);
            const product_tmpl_id = main_product?.raw.product_tmpl_id;
            const product_variants = product_product.filter(product => product.raw.product_tmpl_id === product_tmpl_id);
            let total_qty_available = 0;
            product_variants.forEach((variant) => {
                if (variant.qty_available) {
                    total_qty_available += variant.qty_available;
                }
            });
            this.qty_available = total_qty_available;
          }
    },

    get value() {
        if (this.pos.config.display_stock_setting == true) {
            const current_product_name = this.props.name;
            const move_line = this.pos.move_line;
            const stock_product = this.pos.stock_quant;
            const product_product = this.pos.product_product;
            const current_product = this.props.productId;
            const productId = this.props.productId;
            let on_hand_loc = 0;
            let incoming_loc = 0;
            let outgoing_loc = 0;
            var flag = 0
            this._loadLocationStock(productId).then(() => {
                this.state.on_hand_loc = this.location_stock_quant;
                this.pos.on_hand_loc = this.location_stock_quant;
            });

            const main_product = product_product.find(product => product.product_tmpl_id.id === current_product);
            const main_prod_id = main_product?.id

            move_line.forEach((line) => {
            if (line && line.product_id) {
                if(line.product_id.id == main_prod_id && this.pos.res_setting && this.pos.config.pos_stock_location_id == line.raw.location_dest_id && flag == 0){
                      flag = 1
                      incoming_loc = incoming_loc + line.product_id.incoming_qty;
                }if(line.product_id.id == main_prod_id && this.pos.res_setting && this.pos.config.pos_stock_location_id && this.pos.config.pos_stock_location_id == line.raw.location_id && flag == 0){
                       flag = 1
                      outgoing_loc = outgoing_loc + line.product_id.outgoing_qty;
                }
            }
            });

            this.updateProductDetails().then(() => {
                this.state.main_prod = main_product?.display_name

                this.state.qty_available = this.qty_available;
                this.pos.all_on_hand = this.qty_available;

                this.state.incoming_qty = this.productDetail?.incoming_qty;
                this.pos.all_incoming = this.productDetail?.incoming_qty;

                this.state.outgoing_qty = this.productDetail?.outgoing_qty;
                this.pos.all_outgoing = this.productDetail?.outgoing_qty;

                this.state.incoming_loc = incoming_loc;
                this.pos.incoming_loc = incoming_loc;

                this.state.outgoing_loc = outgoing_loc;
                this.pos.outgoing_loc = outgoing_loc;

                this.state.display_stock = false;
            });
            return { display_stock: this.pos.config.display_stock_setting };
        } else {
            return {display_stock: false};
        }
    }
});
