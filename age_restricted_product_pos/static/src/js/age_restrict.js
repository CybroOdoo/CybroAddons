/** @odoo-module */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { _t } from "@web/core/l10n/translation";
import { RestrictPopup } from "./restrict_popup";

patch(PosStore.prototype, {
    async addProductToCurrentOrder(product, options = {}) {

                //If product is age restricted it shows the popup and on
                //confirming the popup, it will adds to the order line, on
                //rejecting it will cancel the order
                if(product.is_age_restrict == true ){
                    const { confirmed } = await this.popup.add(RestrictPopup,
                        {
                            title: _t('Age Restricted Product !'),
                            body:_t('Attention.! This Product is Under the Age Restricted Category.'),
                        });
                    if (confirmed){
                        super.addProductToCurrentOrder(product, options = {})
                    }
                }
                else{
                    super.addProductToCurrentOrder(product, options = {})
                }
            }
        });
