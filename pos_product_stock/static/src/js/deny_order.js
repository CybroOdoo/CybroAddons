/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { _t } from "@web/core/l10n/translation";

patch(ProductScreen.prototype, {
     setup(){
     super.setup();

     },
     async addProductToOrder(event) {
        const current_product_id = event.id;
        const product_product = this.pos.product_product;
        const stock_product = this.pos.stock_quant;
        const main_product = product_product.find(product => product.id === current_product_id);
        const product_tmpl_id = main_product._raw.product_tmpl_id;
        const product_variants = product_product.filter(product => product._raw.product_tmpl_id === product_tmpl_id);
        let total_qty_available = 0;
        product_variants.forEach(variant => {
                stock_product.forEach(stock => {
                     if (stock.product_id && stock.product_id.id === variant.id) {
                          total_qty_available += stock.available_quantity;
                     }
                });
        });
     if(event.type === 'consu'){
     if(this.pos.res_setting['stock_from'] === 'all_warehouse'){
     let qty_available = 0;
        product_variants.forEach((variant) => {
            if (variant.qty_available) {
                qty_available += variant.qty_available;
            }
        });
        if (this.pos.res_setting['stock_type'] === 'on_hand') {
            if (qty_available <= event.deny) {
             await this.dialog.add(AlertDialog, {
                            title: _t('Deny Order'),
                            body: _t('%s is Out Of Stock', event.name),
             });
            } else {
                        super.addProductToOrder(event);
            }
        }else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
            if (event.outgoing_qty <= event.deny) {
                await this.dialog.add(AlertDialog, {
                    title: _t('Deny Order'),
                    body: _t('%s is Out Of Stock', event.name),
                });
            }else {
                    super.addProductToOrder(event);
            }
        } else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                if (event.incoming_qty <= event.deny) {
                    await this.dialog.add(AlertDialog, {
                        title: _t('Deny Order'),
                        body: _t('%s is Out Of Stock', event.name),
                    });
                }else {
                        super.addProductToOrder(event);
                }
        }
     }else if (this.pos.res_setting['stock_from'] ==='current_warehouse') {
                if (this.pos.res_setting['stock_type'] === 'on_hand') {
                    if (total_qty_available <= event.deny) {
                        await this.dialog.add(AlertDialog, {
                              title: _t('Deny Order'),
                              body: _t('%s is Out Of Stock', event.name),
                        });
                    } else {
                        super.addProductToOrder(event);
                    }
                }else if (this.pos.res_setting['stock_type'] === 'outgoing_qty') {
                    if (event.outgoing_qty <= event.deny) {
                        await this.dialog.add(AlertDialog, {
                            title: _t('Deny Order'),
                            body: _t('%s is Out Of Stock', event.name),
                        });
                    } else {
                        super.addProductToOrder(event);
                    }
                }else if (this.pos.res_setting['stock_type'] === 'incoming_qty') {
                    if (event.incoming_qty <= event.deny) {
                        await this.dialog.add(AlertDialog, {
                            title: _t('Deny Order'),
                            body: _t('%s is Out Of Stock', event.name),
                        });
                    } else {
                        super.addProductToOrder(event);
                    }
                }
     }
     }else {
            super.addProductToOrder(event);
     }

    },
});
