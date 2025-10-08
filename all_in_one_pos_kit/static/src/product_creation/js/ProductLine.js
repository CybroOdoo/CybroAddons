/**@odoo-module **/
import PosComponent from "point_of_sale.PosComponent";
import Registries from "point_of_sale.Registries";
import { Gui } from 'point_of_sale.Gui';
class ProductLine extends PosComponent {//A custom component representing a single line in the product list view.
    get imageUrl() {//Retrieves the URL of the product's image. @returns {string} The URL of the product's image.
        const product = this.props.product;
        return `/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
    }
    async editCurrentProduct() {//Opens the edit product popup for the current product.
        await Gui.showPopup("EditProductPopup", {
            product: this.props.product,
        });
    }
}
ProductLine.template = "ProductLine";
Registries.Component.add(ProductLine);
