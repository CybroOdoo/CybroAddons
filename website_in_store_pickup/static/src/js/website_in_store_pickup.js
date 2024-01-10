/* @odoo-module */
import core from "web.core";
import publicWidget from 'web.public.widget';
import 'website_sale_delivery.checkout';
var QWeb = core.qweb;
/**
 * Extends the websiteSaleDelivery widget to handle store pickup functionality.
 */
publicWidget.registry.websiteSaleDelivery.include({
    /**
     * Handles the click event on the store pickup dropdown.
     *
     * Updates the address display based on the selected store and toggles the
     * visibility of UI elements.
     *
     * @param {Event} ev - The click event.
     */
        _onClickDropDown: async function(ev){
        var addressTemplate = {};
        const selectedStoreId = parseInt(ev.target.selectedOptions[0].dataset.storeId)
        var self = this;
        const address = await this._rpc({
            route: '/shop/update_address',
            params: {
                store_id: selectedStoreId
                },
        }).then(result => {
            this.$el.find('#store_address_section').remove()
            if (result) {
                addressTemplate.address = result.store_id[0].contact_address
            }
        })
        this.$el.find('#shipping_and_billing').after(QWeb.render('StoreAddress', addressTemplate));
        this.$el.find('#shipping_and_billing').hide();
    },
    /**
     * Handles the click event on a carrier option.
     *
     * Performs actions such as checking carrier options, updating UI elements,
     * and dynamically rendering store pickup dropdown.
     *
     * @param {Event} ev - The click event.
     */
    _onCarrierClick:  function(ev){
        var radio = $(ev.currentTarget).find('input[type="radio"]');
        const status = this._rpc({
            route: '/shop/check_carrier',
            params: {
                carrier_id: radio.val(),
            },
        }).then(async data => {
            this.$el.find('#shipping_and_billing').show()
            this.$el.find('#store_address_section').remove()
            if (this.$el.find('#shipping_and_billing'))
                var storeDropdown = this.$el.find('.store-pickup-dropdown');
                if (! data.is_store_pick ){
                    storeDropdown.hide();
                }
                if (data['is_store_pick']){
                    var templateData = {};
                    if (data['store_ids'].length === 0) {
                        templateData.store_all = data['store_id'];
                    }
                    else {
                        templateData.stores = data['store_ids'];
                    }
                    var self = this;
                    if ( storeDropdown.length === 0 ) {
                        await this.$el.find('.list-group').append(QWeb.render('StorePickup', templateData));
                        this.el.querySelector('.store-pickup-dropdown').addEventListener('click',this._onClickDropDown.bind(this) )
                        storeDropdown.on('click', this._onClickDropDown.bind(this))
                    }
                    else {
                        storeDropdown.show()
                    }
                }
        });
        this._super(...arguments)
    }
})
