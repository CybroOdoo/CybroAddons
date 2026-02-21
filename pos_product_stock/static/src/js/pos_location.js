//** @odoo-module */
import { ProductCard } from "@point_of_sale/app/generic_components/product_card/product_card";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { useRef, useState } from "@odoo/owl";

patch(ProductCard.prototype, {
    setup() {
        super.setup();
        this.state = useState({
            qty_available: null,
            incoming_qty: null,
            outgoing_qty: null,
            display_stock: false,
            on_hand_loc: null,
            incoming_loc: null,
            outgoing_loc: null,
        });

        this.pos = usePos();
        this.orm = useService('orm');
    },

    async fetchProductDetails(productId) {
    const product = await this.orm.call("product.product", "read", [[productId], ["name", "id", "incoming_qty","outgoing_qty","qty_available"]]);
     return product[0];
    },

    async updateProductDetails() {
        const productId = this.props.productId;
        if (productId) {
            this.productDetail = await this.fetchProductDetails(productId);
            const product_product = this.pos.product_product;
            const stock_product = this.pos.stock_quant;
            const main_product = product_product.find(product => product.id === productId);
            const product_tmpl_id = main_product.raw.product_tmpl_id;
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
        if (this.pos.res_setting.display_stock == true) {
            const current_product = this.props.productId;
            const current_product_name = this.props.name;
            const move_line = this.pos.move_line;
            const stock_product = this.pos.stock_quant;
            const product_product = this.pos.product_product;
            const product_template_id = this.props.product.product_tmpl_id.id;
            const productId = this.props.productId;
            let on_hand_loc = 0;
            let incoming_loc = 0;
            let outgoing_loc = 0;
            var flag = 0;

            const main_product = product_product.find(
                    p => p.product_tmpl_id.id === product_template_id);
                const main_prod_id = main_product?.id

                if (main_product) {
                    const tmpl_id = main_product.raw.product_tmpl_id;

                    const variants = product_product.filter(
                        p => p.raw.product_tmpl_id === tmpl_id
                    );

                    variants.forEach(v => {
                        on_hand_loc += this.pos.location_stock_map?.[v.id] || 0;
                    });
                }

            this.state.on_hand_loc = on_hand_loc;

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
                this.state.incoming_qty = this.productDetail?.incoming_qty;
                this.state.outgoing_qty = this.productDetail?.outgoing_qty;
                this.state.incoming_loc = incoming_loc;
                this.state.outgoing_loc = outgoing_loc;
                this.state.display_stock = false;
            });

            return {
                display_stock: this.pos.res_setting.display_stock
            };

        } else {
            return {
                display_stock: false
            };
        }
    }
});

