/**@odoo-module **/
import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";
import { Gui } from 'point_of_sale.Gui';

class ProductLine extends PosComponent {
    /**
     * Get the URL for the product image.
     * @returns {string} The URL of the product image.
     */
    get imageUrl() {
        const product = this.props.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
    }
    /**
     * Edit the current product by showing the EditProductPopup.
     */
    async editCurrentProduct() {
        await this.showPopup("EditProductPopup", {
            product: this.props.product,
        });
    }
}
ProductLine.template = "ProductLine";
Registries.Component.add(ProductLine);
