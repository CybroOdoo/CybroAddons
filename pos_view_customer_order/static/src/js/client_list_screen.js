odoo.define('pos_view_customer_order.inherited_partner_list_screen', function(require) {
    'use strict';
const ClientListScreen = require('point_of_sale.ClientListScreen');
const Registries = require('point_of_sale.Registries');
/** Extends the PartnerListScreen and added additional function getOrders
    to view particular customers past orders from customers portal **/
const GetOrderClientListScreen = (ClientListScreen) =>
        class extends ClientListScreen {
            constructor() {
                super(...arguments);
                }
            goToOrders() {
                // Function to get particular partners order from pos
                this.showScreen('TicketScreen');
                this.back(true);
                this.back(true);
                const partner = this.state.editModeProps.partner;
                const partnerHasActiveOrders = this.env.pos
                    .get_order_list()
                    .some((order) => order.partner?.id === partner.id);
                console.log("partner",partnerHasActiveOrders)
                const searchDetails = partner ? { fieldName: 'CUSTOMER', searchTerm: partner.name } : {};
                this.showScreen('TicketScreen', {
                ui: { filter: partnerHasActiveOrders ? "" : "SYNCED", searchDetails },
            });
            }
        };
Registries.Component.extend(ClientListScreen, GetOrderClientListScreen);
});
