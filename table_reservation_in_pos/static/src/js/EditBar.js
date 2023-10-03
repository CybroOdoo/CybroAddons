odoo.define('table_reservation_in_pos.Reservation', function (require) {
    'use strict';
    const FloorScreen = require('pos_restaurant.FloorScreen');
    const Registries = require('point_of_sale.Registries');
    /**
     *The ReserveTable constant is defined as a higher-order function that
     *takes the FloorScreen class as a parameter and returns a new class that
     *extends FloorScreen.
     *This class will add two additional functions: reserve() and un_reserve().
     */
    const ReserveTable = (FloorScreen) =>
       class extends FloorScreen {
       async reserve() {
            // Function for reserve table in pos with entering details
            if (!this.selectedTable) return;
            if (this.selectedTable.reserved){
                await this.showPopup('ErrorPopup', {
                    title: this.env._t('Reserved'),
                    body: this.env._t('This table is reserved'),
                });
                return;
            }
            const selectedTable = this.selectedTable;
            const { confirmed, payload: details } = await this.showPopup('TextAreaPopup', {
                startingValue: '',
                title: this.env._t('Reservation Details ?'),
            });
            if (!confirmed) return;
            selectedTable.reserved = true;
            selectedTable.reservation_details = details;
            await this._save(selectedTable);
        }
       async vieInfo() {
            // Function for view reservation details and un reserve table in pos
            const selectedTable = this.selectedTable;
            if (selectedTable.reserved){
                var info = selectedTable.reservation_details
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Reservation Details'),
                    body: this.env._t(info),
                    confirmText: this.env._t('UnReserve'),
                });
                if (confirmed){
                    const { confirmed } = await this.showPopup('ConfirmPopup', {
                        title: this.env._t('Confirm Unreservation'),
                        body: this.env._t('Are you sure you want to unreserve this table?'),
                        confirmText: this.env._t('Yes'),
                        cancelText: this.env._t('No'),
                    });
                    if (confirmed){
                        selectedTable.reserved = false;
                        selectedTable.reservation_details = '';
                        await this._save(selectedTable);
                    }
                }
                return;
            }
       }
       async un_reserve() {
            // Function for un reserve reserved table in pos
            if (!this.selectedTable) return;
            const selectedTable = this.selectedTable;
            if (selectedTable.reserved){
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Confirm Unreservation'),
                    body: this.env._t('Are you sure you want to unreserve this table?'),
                    confirmText: this.env._t('Yes'),
                    cancelText: this.env._t('No'),
                });
                if (confirmed){
                    selectedTable.reserved = false;
                    selectedTable.reservation_details = '';
                    await this._save(selectedTable);
                }
            }
        }
        };
    Registries.Component.extend(FloorScreen, ReserveTable);
});