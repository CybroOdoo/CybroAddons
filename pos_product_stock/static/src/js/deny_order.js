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
             if(event.type === 'consu'){
                 if(this.pos.config.location_from === 'all_warehouse'){
                    if (this.pos.config.stock_product === 'on_hand') {
                        if (this.pos.all_on_hand <= event.deny) {
                         await this.dialog.add(AlertDialog, {
                                        title: _t('Deny Order'),
                                        body: _t('%s is Out Of Stock', event.name),
                         });
                        } else {super.addProductToOrder(event);
                        }
                    }else if (this.pos.config.stock_product === 'outgoing_qty') {

                        if (this.pos.all_outgoing <= event.deny) {
                            await this.dialog.add(AlertDialog, {
                                title: _t('Deny Order'),
                                body: _t('%s is Out Of Stock', event.name),
                            });
                        }else {
                                super.addProductToOrder(event);
                        }
                    } else if (this.pos.config.stock_product === 'incoming_qty') {
                            if (this.pos.all_incoming <= event.deny) {
                                await this.dialog.add(AlertDialog, {
                                    title: _t('Deny Order'),
                                    body: _t('%s is Out Of Stock', event.name),
                                });
                            }else {
                                    super.addProductToOrder(event);
                            }
                    }
                 }
                 else if (this.pos.config.location_from ==='current_warehouse') {
                            if (this.pos.config.stock_product === 'on_hand') {
                                if (this.pos.on_hand_loc <= event.deny) {
                                    await this.dialog.add(AlertDialog, {
                                          title: _t('Deny Order'),
                                          body: _t('%s is Out Of Stock', event.name),
                                    });
                                } else {
                                    super.addProductToOrder(event);
                                }
                            }else if (this.pos.config.stock_product === 'outgoing_qty') {
                                if (this.pos.outgoing_loc <= event.deny) {
                                    await this.dialog.add(AlertDialog, {
                                        title: _t('Deny Order'),
                                        body: _t('%s is Out Of Stock', event.name),
                                    });
                                } else {
                                    super.addProductToOrder(event);
                                }
                            }else if (this.pos.config.stock_product === 'incoming_qty') {
                                if (this.pos.incoming_loc <= event.deny) {
                                    await this.dialog.add(AlertDialog, {
                                        title: _t('Deny Order'),
                                        body: _t('%s is Out Of Stock', event.name),
                                    });
                                } else {
                                    super.addProductToOrder(event);
                                }
                            }
                 }
                 else{ super.addProductToOrder(event);}
             }else {super.addProductToOrder(event);}
        },
    });
