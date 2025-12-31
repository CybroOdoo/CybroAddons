/** @odoo-module **/
import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";
import { renderToElement } from "@web/core/utils/render";


publicWidget.registry.index3Subscription = publicWidget.Widget.extend({
      selector: '.sustainable_product',
      events: {
        'click .btn_demo': '_onThreeDotsClick',
        'click .modal .close': '_onModalClose',
      },

      start: function(){
          console.log('Theme Diva Product');
          this._fetch_diva_products()
      },
      async _fetch_diva_products(){
          console.log('_fetch_diva_products');
          const result = await rpc('/fetch_diva_products', {});
          console.log(result.diva_products,result.length)

      },
      _onThreeDotsClick: function () {
            console.log('_onThreeDotsClick');
            $('#payModal').fadeIn(); // Show the modal
      },
      _onModalClose: function () {
          console.log('_onModalClose');
            $('#payModal').fadeOut(); // Hide the modal
      },
});