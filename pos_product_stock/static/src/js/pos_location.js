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
        display_stock: false
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
        const product_tmpl_id = main_product._raw.product_tmpl_id;
        const product_variants = product_product.filter(product => product._raw.product_tmpl_id === product_tmpl_id);
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
            let qty = 0;
            let on_hand = 0;
            let outgoing = 0;
            let incoming = 0;
            const main_product = product_product.find(product => product.id === current_product);
            const product_tmpl_id = main_product._raw.product_tmpl_id;
            const product_variants = product_product.filter(product => product._raw.product_tmpl_id === product_tmpl_id);
            stock_product.forEach((product) => {
                  if (product && product.product_id) {
                      const product_id = product.product_id.id;
                      const is_variant = product_variants.some(variant => variant.id === product_id);
                      if (product_id === current_product || is_variant) {
                            qty += product.available_quantity;
                            on_hand += product.quantity;
                      }
                  }
            });
            move_line.forEach((line) => {
            if (line && line.product_id) {
                if(line.product_id.id == current_product && this.pos.res_setting && this.pos.res_setting._raw.stock_location_id[1] == line._raw.location_dest_id[1]){
                       incoming = incoming + line.product_id.incoming_qty;
                }if(line.product_id.id == current_product && this.pos.res_setting && this.pos.res_setting._raw.stock_location_id && this.pos.res_setting._raw.stock_location_id[1] == line._raw.location_id[1]){
                      outgoing = outgoing + line.product_id.outgoing_qty;
                }
            }
            });

            if (!this.props.available) {
                this.props.available = qty
            }
            if (!this.props.on_hand) {
                this.props.on_hand = on_hand;
            }
            if (!this.props.outgoing) {
                this.props.outgoing = outgoing
            }
            if (!this.props.incoming) {
                this.props.incoming_loc = incoming
            }

            this.updateProductDetails().then(() => {
            this.state.qty_available = this.qty_available
            this.state.incoming_qty = this.productDetail.incoming_qty
            this.state.outgoing_qty = this.productDetail.outgoing_qty
            });
            this.state.display_stock = true;
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

