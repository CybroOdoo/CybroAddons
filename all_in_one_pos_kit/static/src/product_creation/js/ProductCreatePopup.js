/**@odoo-module **/
import AbstractAwaitablePopup from "point_of_sale.AbstractAwaitablePopup";
import Registries from "point_of_sale.Registries";
import { isConnectionError } from "point_of_sale.utils";
import {useListener} from "@web/core/utils/hooks";
let img = "";
let base64_img = "";
class CreateProductPopup extends AbstractAwaitablePopup {// A custom popup component for creating a new product.
  setup() {//Sets up the component by initializing the event listener.
    super.setup();
    useListener("change", "#img_field", this._onChangeImgField);
  }
  async _onChangeImgField(ev) {
    // This function will work when adding image to the image field
    try {
      const reader = new FileReader();
      reader.readAsDataURL(ev.target.files[0]);
      reader.onload = await
      function () {
        img = reader.result;
        base64_img = reader.result.toString().replace(/^data:(.*,)?/, "");
        const myTimeout = setTimeout(() => {
          let element =
            "<img src=" + img + " style='max-width: 150px;max-height: 150px;'/>";
          $(ev.srcElement.offsetParent).find('.product-img-create-popup').append($(element));
        }, 100);
      };
      reader.onerror = (error) =>
        reject(() => {
          console.log("error", error);
        });
    } catch (error) {
      if (isConnectionError(error)) {
        this.showPopup("ErrorPopup", {
          title: this.env._t("Network Error"),
          body: this.env._t("Cannot access Product screen if offline."),
        });
      } else {
        throw error;
      }
    }
  }
  async confirm(ev) {//Confirms the creation of the product.
    let img = $(this.el).find("#img_field")[0].value;
    let name = $(this.el).find("#display_name")[0].value;
    let price = $(this.el).find("#list_price")[0].value;
    let cost = $(this.el).find("#cost_price")[0].value;
    let category = $(this.el).find("#product_category")[0].value;
    let barcode = $(this.el).find("#barcode")[0].value;
    let default_code = $(this.el).find("#default_code")[0].value;
    let values = {};
    if (base64_img) {
      values["image_1920"] = base64_img;
    }
    if (name) {
      values["name"] = name;
    }
    if (cost) {
      values["standard_price"] = cost;
    }
    if (price) {
      values["lst_price"] = price;
    }
    if (category) {
      values["pos_categ_id"] = category;
    }
    if (barcode) {
      values["barcode"] = barcode;
    }
    if (default_code) {
      values["default_code"] = default_code;
    }
    values["available_in_pos"] = true;
    await this.rpc({
      model: "product.product",
      method: "create",
      args: [values],
    }).then((result) => {
      if (result) {
        this.showNotification(_.str.sprintf(this.env._t('%s - Product Created'), name), 3000);
      } else {
        this.showNotification(_.str.sprintf(this.env._t('%s - Product Creation Failed'), name), 3000);
      }
    });
    this.env.posbus.trigger("close-popup", {
      popupId: this.props.id,
      response: {
        confirmed: false,
        payload: null,
      },
    });
  }
}
CreateProductPopup.template = "CreateProductPopup";
Registries.Component.add(CreateProductPopup);
