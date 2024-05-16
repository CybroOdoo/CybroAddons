/**@odoo-module **/
import { Component , useState } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { CreateProductPopup } from "@pos_product_create_edit/js/ProductCreatePopup";
import { onWillStart} from "@odoo/owl";

export class ProductLine extends Component {
static template = "pos_product_create_edit.ProductLine";
    setup() {
    super.setup();
    this.pos = usePos();
    this.popup = useService("popup")
    this.orm = useService("orm")
    this.state = useState({
    product: this.props.product
    });
    onWillStart(async () => {
            await this.imageUrl();
        });
    }

   imageUrl() {
    const product = this.props.product;
     this.state.product.imageUrl=`/web/image?model=product.product&field=image_128&id=${product.id}&unique=${product.write_date}`;
  }
  async editCurrentProduct() {
     const { confirmed, payload } = await this.popup.add(CreateProductPopup, {
      product: this.props.product,
    });

    if (confirmed) {
           var b= await this.orm.call("product.product", "create_from_ui", [payload]);
            let pos_product =  await this.orm.call("pos.session", "get_pos_ui_product_product_by_params",  [odoo.pos_session_id, {domain: [['id', '=', b]]}]);
            this.state.product = pos_product[0];
            this.props.product = pos_product[0];
            this.imageUrl()

    }

}
}
