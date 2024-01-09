odoo.define('website_portal_rfq.customer_portal', function (require) {
    var ajax = require('web.ajax');
    var publicWidget = require('web.public.widget');

    publicWidget.registry.AdvancedPortalImport = publicWidget.Widget.extend({
        selector: '.o_portal_wrap',
        events: {
            'click #add_image': '_onClickAddProduct',
            'click .delete_row': '_onClickDeleteRow',
            'click .send_rfq_request1': '_onClickSubmit',
            'change .add_product_images': '_onChangeProduct',
            'change .quantity': '_onChangeQuantity',
        },

//         This will help add products from the portal to create a new order
        _onClickAddProduct: async function (e) {
            var rowCount = this.$("#image_table tr").length;
            if (rowCount === 0) {
                this.$("#image_table").append('<tr><td colspan="4">Add Products</td></tr>');
                return;
            }
            var allRowsHaveProducts = true; // Flag to track if all rows have products
            // Loop through each row in the table
            this.$("#image_table tr.products").each(function () {
                var productSelect = $(this).find("select.add_product_images");
                if (productSelect.val() === "") {
                    allRowsHaveProducts = false;
                    return false;
                }
            });
            if (!allRowsHaveProducts) {
                alert("Please select a product for all rows.");
                return;
            }
            rowCount++;
            var rowId = "row_" + rowCount;
            var imageId = "image_" + rowCount;
            var productId = "product_" + rowCount;
            var uomId = "uom_" + rowCount;
            var quantityId = "quantity_" + rowCount;
            var descriptionId = "description_" + rowCount;
            table_data='<tr id="' + rowId + '" class="products"> <td style="padding:10px;display: flex; justify-content: center; align-items: center;" class="td-product_name1"><img src="/website_portal_rfq/static/src/img/cam1.png" id="' + imageId + '" value="Product Image" name="' + imageId + '" class="image_11"/></td><td style="padding:10px;"><select class="add_product_images form-control se-form-control select2" name="' + productId + '" id="' + productId + '" required="required"><option value="">Select Products...</option>';
            await ajax.jsonRpc('/my/product_details', 'call', {}).then(function (data) {
                for (let i = 0; i < data.product_id.length; i++) {
                    table_data+='<option value='+data.product_id[i][1]+'>'+data.product_id[i][0]+'</option>';
                }
            });
            table_data+='</select></td>'
            table_data+='<td style="padding:10px;"><select class="add_uom form-control se-form-control" name="' + uomId + '" id="' + uomId + '" required="required"><option value="">Select UoM...</option></select></td>'
            table_data+='<td style="padding:10px;" class="quantity td-product_name" name="quantity"><input type="text" class="form-control" value="1" required="required" name="' + quantityId + '" id="' + quantityId + '"/></td><td style="padding-top:10px;padding-right: 10px;padding-bottom: 10px;padding-left: 35px;" class="td-action"><a href="#" aria-label="Remove product" title="Remove Product" class="delete_row no-decoration"><small><i class="fa fa-trash-o"></i></small></a></td></tr>';
            this.$("#image_table").append(table_data);
        },

        // Delete the row if not needed
        _onClickDeleteRow: function (e) {
            var row = this.$(e.currentTarget).parent().parent()[0].id;
            this.$('#' + row).remove();
        },

        // Submit the request from the portal
        _onClickSubmit: function (e) {
            e.preventDefault();
            var productCount = this.$("#image_table tr.products").length;
            if (productCount === 0) {
                alert("Please add at least one product before submitting the form.");
                return;
            }
            // Loop through each row in the table
            var allRowsHaveProducts = true;
            this.$("#image_table tr.products").each(function () {
                var productSelect = $(this).find("select.add_product_images");
                if (productSelect.val() === "") {
                    allRowsHaveProducts = false;
                    return false;
                }
            });
            if (!allRowsHaveProducts) {
                alert("Please select a product for all rows.");
                return;
            }
            var form = this.$("#my_send_request");
            form.submit();
        },
//        Check if the input is a valid number
        _onChangeQuantity:function (e) {
             var inputValue = e.target.value;
              var isNumeric = /^[-+]?(\d+(\.\d*)?|\.\d+)([eE][-+]?\d+)?$/.test(inputValue);
              if (!isNumeric) {
                alert("Please enter a valid numeric value for quantity.");
                // Set it back to the default value
                e.target.value = "1";
              }
        },

        // Add image of the product when changing it
        _onChangeProduct: function (e) {
            const row = this.$(e.currentTarget).closest('tr');
            const uomSelect = row.find('select.add_uom');
           // Update the image
            const img = row.find('img')[0];
            ajax.jsonRpc('/my/product_image', 'call', {
                'onchange_product_id': e.currentTarget.value,
            }).then(function (data) {
                img.src = data ? 'data:image/jpeg;base64,' + data : '/website_portal_rfq/static/src/img/cam1.png';
            });
            // Fetch and update the UOM options based on the selected product
            const productId = e.currentTarget.value;
            if (productId) {
                ajax.jsonRpc('/my/product_uom', 'call', {
                    'product_id': productId,
                }).then(function (data) {
                    // Update the UOM select options
                    uomSelect.empty();
                    for (let i = 0; i < data.uom_ids.length; i++) {
                        uomSelect.append('<option value="' + data.uom_ids[i][0] + '">' + data.uom_ids[i][1] + '</option>');
                    }
                });
            } else {
                // Clear UOM options if no product is selected
                uomSelect.empty();
                uomSelect.append('<option value="">Select UoM...</option>');
            }
        },
    });
});
