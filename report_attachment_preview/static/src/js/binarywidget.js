/** @odoo-module **/
import { Many2ManyBinaryField } from "@web/views/fields/many2many_binary/many2many_binary_field"
import { patch } from "@web/core/utils/patch";
/**
  This module patches the onClickURL method of the Many2ManyBinaryField class
  to open URLs in a new tab when clicked.
 **/
patch(Many2ManyBinaryField.prototype, {
    onClickURL(id) {
         window.open(`/web/content/${id}?download=true`)
    }
})
