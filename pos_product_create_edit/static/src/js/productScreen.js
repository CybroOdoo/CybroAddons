/**@odoo-module **/
import { ControlButtonsMixin } from "@point_of_sale/app/utils/control_buttons_mixin";
import { registry } from "@web/core/registry";
import { Component, useState , onWillStart} from "@odoo/owl";
import { onWillUnmount, useRef, onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { ProductLine } from "@pos_product_create_edit/js/ProductLine";
import { useService } from "@web/core/utils/hooks";
import { CreateProductPopup } from "@pos_product_create_edit/js/ProductCreatePopup";


class ProductListScreen extends Component {
static template = "pos_product_create_edit.ProductListScreen";
static components = { ProductLine };

  setup() {
    super.setup();
        this.pos = usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
        this.searchWordInputRef = useRef("search-word-input-product");
        this.state = useState({
        search: null,
        products:[]
    });
     onWillStart(async () => {
            this.state.products = await this.get_products();
        });
  }

  async createProduct() {
     const { confirmed, payload } = await this.popup.add(CreateProductPopup, {
      product: this.props.product,
    });

    if (confirmed) {
            var b= await this.orm.call("product.product", "create_from_ui", [payload]);
            let pos_product =  await this.orm.call("pos.session", "get_pos_ui_product_product_by_params",  [odoo.pos_session_id, {domain: [['id', '=', b]]}]);
            this.state.products = [pos_product[0], ...this.state.products]
    }
  }
  async get_products() {
  let list;
  if (this.state.search && this.state.search.trim() !== "") {
    list = this.pos.db.search_product_in_category(
      0,
      this.state.search.trim()
    );
  } else {
    list = this.pos.db.get_product_by_category(0);
  }
  if (!list || list.length === 0) {
    list = this.pos.db.get_product_by_category(0);
  }
  var abc=list.sort(function (a, b) {
    return a.display_name.localeCompare(b.display_name);
  });
  return abc
}
  async updateProductList(event) {
    this.state.search = event.target.value;
    if (event.code === "Enter") {
      this._onPressEnterKey();
    } else {
        var result = await this.get_products();
        this.state.products = result;
      this.render(true);
    }
  }
  async _onPressEnterKey() {
    if (!this.state.search) return;
    if (!this.pos.isEveryProductLoaded) {
      const result = await this.get_products();
      this.state.products = await this.get_products();
       this.env.services.notification.add(_t('%s Product(s) found for "%s".', { thread_name: thread.name }),
            { type: "success" })
      if (!result.length) this._clearSearch();
    }
  }
  async _clearSearch() {
    this.searchWordInputRef.el.value = "";
    this.state.search = "";
    var result = await this.get_products();
    this.state.products = result;
    this.render(true);
  }

  back() {
    this.pos.showScreen('ProductScreen');
    }
}
registry.category("pos_screens").add("ProductListScreen", ProductListScreen);
