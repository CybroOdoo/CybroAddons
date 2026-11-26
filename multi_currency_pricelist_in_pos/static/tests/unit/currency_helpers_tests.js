/** @odoo-module **/

import {
    convertAmount,
    convertOrderAmountToBaseCurrency,
    getCurrencyRounding,
    getPricelistCurrency,
    isMultiCurrencyPricelistEnabled,
} from "@multi_currency_pricelist_in_pos/app/utils/currency_helpers";

QUnit.module("multi_currency_pricelist_in_pos > currency helpers", () => {
    function makeFixture({ enabled = true, pricelistCurrencyId = 2 } = {}) {
        const baseCurrency = {
            id: 1,
            name: "USD",
            symbol: "$",
            position: "before",
            rounding: 0.01,
            rate: 1,
            decimal_places: 2,
        };
        const pricelistCurrency = {
            id: 2,
            name: "EUR",
            symbol: "EUR",
            position: "after",
            rounding: 0.05,
            rate: 0.5,
            decimal_places: 3,
        };
        const pricelist = {
            id: 10,
            currency_id: [pricelistCurrencyId, "Target Currency"],
        };
        const order = { pricelist: pricelist };
        const pos = {
            currency: baseCurrency,
            config: {
                use_pricelist: true,
                enable_multi_currency_pricelist: enabled,
            },
            get_order() {
                return order;
            },
            getCurrencyById(currencyId) {
                if (currencyId === baseCurrency.id) {
                    return baseCurrency;
                }
                if (currencyId === pricelistCurrency.id) {
                    return pricelistCurrency;
                }
                return null;
            },
        };
        order.pos = pos;
        return { pos, order, pricelist, baseCurrency, pricelistCurrency };
    }

    QUnit.test("feature flag detection follows the POS config", async (assert) => {
        const enabledFixture = makeFixture({ enabled: true });
        const disabledFixture = makeFixture({ enabled: false });

        assert.true(isMultiCurrencyPricelistEnabled(enabledFixture.pos));
        assert.false(isMultiCurrencyPricelistEnabled(disabledFixture.pos));
    });

    QUnit.test("pricelist currency falls back to base currency when feature is disabled", async (assert) => {
        const { pos, baseCurrency, pricelistCurrency } = makeFixture({ enabled: false });

        assert.deepEqual(getPricelistCurrency(pos), baseCurrency);
        assert.strictEqual(getPricelistCurrency(pos).id, baseCurrency.id);
        assert.notStrictEqual(getPricelistCurrency(pos).id, pricelistCurrency.id);
    });

    QUnit.test("currency helpers use the selected pricelist currency when enabled", async (assert) => {
        const { pos, pricelistCurrency } = makeFixture({ enabled: true });

        assert.deepEqual(getPricelistCurrency(pos), pricelistCurrency);
        assert.strictEqual(getCurrencyRounding(pos), pricelistCurrency.rounding);
    });

    QUnit.test("amount conversion and base currency export conversion use currency rates", async (assert) => {
        const { pos, order, baseCurrency, pricelistCurrency } = makeFixture({ enabled: true });

        assert.strictEqual(convertAmount(pos, 10, baseCurrency, pricelistCurrency), 5);
        assert.strictEqual(convertAmount(pos, 10, pricelistCurrency, baseCurrency), 20);
        assert.strictEqual(convertOrderAmountToBaseCurrency(order, 1.333), 2.67);
    });
});
