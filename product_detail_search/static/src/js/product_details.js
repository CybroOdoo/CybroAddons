/** @odoo-module **/

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');
    class ProductDetails extends PosComponent {
        setup(){
            super.setup();
            if (this.props.product_details==false){
            this.product_details=false
            }
            else
            {
             this.product_details =  this.props.product_details;
            }
        }
        //To see the Find product Screen
        back() {
            this.showScreen('FindProductScreen');
        }
    };
  ProductDetails.template = 'ProductDetails';
  Registries.Component.add(ProductDetails);
  return ProductDetails;
