/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { patch } from "@web/core/utils/patch";

//Created product magnifying widget
export class MagnifyProductPopup extends AbstractAwaitablePopup {
    static template = "MagnifyProductPopup";
    static defaultProps = {
        confirmKey: false
    };
    //Supering setup() for assigning value
    setup() {
        super.setup();
        Object.assign(this, this.props.product);
    }
    //Get the image of clicked product
    get largeImageUrl() {
        const product = this;
        return `/web/image?model=product.product&field=image_1920&id=${product.id}&write_date=${product.write_date}&unique=1`;
    }
    //Closing the widget
    cancel() {
        this.props.close();
    }
}
