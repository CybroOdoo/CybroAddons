/**
 * POS Multi Currency Payment extension for PaymentScreen.
 * It allows cashiers to accept payments in foreign currencies, view conversion
 * rates against company currency, and add payment lines with foreign currency details.
 */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { onWillStart, proxy } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { _t } from "@web/core/l10n/translation";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");

        this.multi_currency = proxy({
            showOptions: false,
            showConversion: false,
            currencies: [],
            selectedCurrencyId: "",
            rate: 1,
            rate_val: 0,
            usd_val: 0,
            name: "",
            symbol: "",
            total: 0,
            inputAmount: "",
            hasInputError: false,
        });

        onWillStart(async () => {
            if (this.pos.config.enable_multicurrency) {
                const settings = await this.orm.call(
                    "pos.config",
                    "get_config_settings",
                    [this.pos.config.id],
                    {}
                );

                if (settings && settings.length > 0) {
                    this.multi_currency.currencies = settings;
                }
            }
        });
    },

    /**
     * Toggle visibility of multi-currency options panel.
     *
     * @param {Event} event
     */
    toggleMultiCurrency(event) {
        this.multi_currency.showOptions = event.target.checked;
        if (!this.multi_currency.showOptions) {
            this.multi_currency.showConversion = false;
            this.multi_currency.hasInputError = false;
        }
    },

    /**
     * Handle currency selection from dropdown and fetch exchange rate details.
     *
     * @param {Event} event
     */
    async onSelectCurrency(event) {
        const selectedId = event.target.value;
        if (!selectedId || selectedId === "none") {
            this.multi_currency.showConversion = false;
            this.multi_currency.selectedCurrencyId = "";
            return;
        }

        this.multi_currency.selectedCurrencyId = selectedId;
        this.multi_currency.hasInputError = false;

        const order = this.currentOrder || this.pos.getOrder();
        const totalValue = order?.priceIncl ?? order?.totalDue ?? 0;

        const currencyData = await this.orm.call(
            "pos.config",
            "get_selected_currency",
            [selectedId],
            {}
        );

        if (currencyData && currencyData.length > 0) {
            const curr = currencyData[0];
            const rate = curr.rate || 1;
            const rateVal = curr.rate_val ?? curr.usd_val ?? rate;
            this.multi_currency.name = curr.name;
            this.multi_currency.symbol = curr.symbol;
            this.multi_currency.rate = rate;
            this.multi_currency.rate_val = rateVal;
            this.multi_currency.usd_val = rateVal;
            this.multi_currency.total = Math.round(rate * totalValue * 100) / 100;
            const remainingDue = order?.remainingDue ?? totalValue;
            const foreignRemaining = Math.round(rate * remainingDue * 100) / 100;
            this.multi_currency.inputAmount = foreignRemaining > 0 ? String(foreignRemaining) : "";
            this.multi_currency.showConversion = true;
        }
    },

    /**
     * Add a payment line in the selected foreign currency.
     *
     * @param {Object} [ev] - Optional payment method configuration object.
     */
    async multi_currency_payment_line(ev) {
        if (!this.pos.config.enable_multicurrency) {
            return;
        }

        const inputEl = document.querySelector(".multicurrency_input");
        const rawAmount = this.multi_currency.inputAmount || inputEl?.value;
        const amountVal = parseFloat(rawAmount);
        const order = this.currentOrder || this.pos.getOrder();
        const remainingDue = order?.remainingDue ?? order?.totalDue ?? 0;
        const totalVal = order?.priceIncl ?? order?.totalDue ?? 0;

        if (
            !isNaN(amountVal) &&
            amountVal > 0 &&
            this.multi_currency.rate &&
            (totalVal > 0 || remainingDue > 0)
        ) {
            const cashMethod = this.payment_methods_from_config?.find((m) => m.type === "cash");
            const paymentMethod = (ev && ev.id ? ev : null) || cashMethod;

            if (!paymentMethod) {
                this.notification?.add(
                    _t("No cash payment method configured for this Point of Sale."),
                    { type: "danger" }
                );
                return;
            }

            await this.addNewPaymentLine(paymentMethod);
            const updateAmount = amountVal / this.multi_currency.rate;
            const selectedLine = this.selectedPaymentLine;

            if (selectedLine) {
                selectedLine.setAmount(updateAmount);
                selectedLine.converted_currency = {
                    name: this.multi_currency.name,
                    symbol: this.multi_currency.symbol,
                    rate: this.multi_currency.rate,
                    currency_id: this.multi_currency.selectedCurrencyId,
                    amount: amountVal,
                };
                selectedLine.payment_currency = this.multi_currency.name;
                selectedLine.currency_amount = amountVal;
                selectedLine.update?.({
                    payment_currency: this.multi_currency.name,
                    currency_amount: amountVal,
                });
            }

            if (order) {
                order.converted_currency = {
                    name: this.multi_currency.name,
                    symbol: this.multi_currency.symbol,
                    rate: this.multi_currency.rate,
                    amount: amountVal,
                    converted_total: this.multi_currency.total,
                };
            }

            this.multi_currency.showConversion = false;
            this.multi_currency.inputAmount = "";
            this.multi_currency.hasInputError = false;
        } else {
            this.multi_currency.hasInputError = true;
        }
    },

    /**
     * Recalculate converted currency values when selected payment line is updated.
     * Uses the rate and currency details of the line's own currency rather than
     * the currently selected dropdown rate.
     *
     * @override
     * @param {number|boolean} [amount=false]
     */
    updateSelectedPaymentline(amount = false) {
        super.updateSelectedPaymentline(...arguments);
        if (this.pos.config.enable_multicurrency && this.selectedPaymentLine) {
            const line = this.selectedPaymentLine;
            const conv = line.converted_currency;
            if (conv) {
                const currencyName = conv.name || line.payment_currency;
                const currencyId = conv.currency_id;
                const matchedCurrency = this.multi_currency.currencies?.find(
                    (c) => (currencyId && c.id === currencyId) || (currencyName && c.name === currencyName)
                );
                const lineRate = conv.rate || matchedCurrency?.rate;
                const lineSymbol = conv.symbol || matchedCurrency?.symbol || "";

                if (lineRate && lineRate > 0) {
                    const changeAmount = Math.round(line.amount * lineRate * 100) / 100;
                    line.converted_currency = {
                        ...conv,
                        name: currencyName,
                        symbol: lineSymbol,
                        rate: lineRate,
                        amount: changeAmount,
                    };
                    line.payment_currency = currencyName;
                    line.currency_amount = changeAmount;
                    line.update?.({
                        payment_currency: currencyName,
                        currency_amount: changeAmount,
                    });
                }
            }
        }
    },

    /**
     * Ensure multi-currency values are synchronized on payment lines when validating.
     *
     * @override
     * @param {Object} [args={}] - Validation arguments.
     * @returns {Promise<any>}
     */
    async onClickValidate(args = {}) {
        const order = this.currentOrder || this.pos.getOrder();
        if (order && order.payment_ids) {
            order.payment_ids.forEach((line) => {
                if (line.converted_currency) {
                    const cName = line.converted_currency.name;
                    const cAmount = line.converted_currency.amount;
                    line.payment_currency = cName;
                    line.currency_amount = cAmount;
                    line.update?.({
                        payment_currency: cName,
                        currency_amount: cAmount,
                    });
                }
            });
        }
        return await super.onClickValidate(...arguments);
    },
});
