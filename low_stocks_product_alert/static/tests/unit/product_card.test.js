/** @odoo-module **/

import { describe, expect, test } from "@odoo/hoot";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import "@low_stocks_product_alert/js/product_card";

describe("ProductCard Low Stock Alert - JS Unit Tests", () => {
    describe.current.tags("desktop");

    // -------------------------------------------------------------------------
    // 1. displayStockAlert getter tests
    // -------------------------------------------------------------------------
    describe("ProductCard.displayStockAlert", () => {
        const getDisplayStockAlert = (card) => {
            const getter = Object.getOwnPropertyDescriptor(
                ProductCard.prototype,
                "displayStockAlert"
            ).get;
            return getter.call(card);
        };

        test("returns false when props.product is null or undefined", () => {
            expect(getDisplayStockAlert({ props: {} })).toBe(false);
            expect(getDisplayStockAlert({ props: { product: null } })).toBe(false);
            expect(getDisplayStockAlert({ props: { product: undefined } })).toBe(false);
        });

        test("returns true when product.alert_state is true", () => {
            const card = {
                props: {
                    product: { id: 1, alert_state: true, alert_tag: "5" },
                },
            };
            expect(getDisplayStockAlert(card)).toBe(true);
        });

        test("returns false when product.alert_state is false", () => {
            const card = {
                props: {
                    product: { id: 1, alert_state: false, alert_tag: false },
                },
            };
            expect(getDisplayStockAlert(card)).toBe(false);
        });

        test("returns true when alert_state is undefined but valid alert_tag exists", () => {
            const card = {
                props: {
                    product: { id: 2, alert_tag: "3" },
                },
            };
            expect(getDisplayStockAlert(card)).toBe(true);
        });

        test("returns false when alert_state and alert_tag are absent", () => {
            const card = {
                props: {
                    product: { id: 3, qty_available: 5 },
                },
            };
            expect(getDisplayStockAlert(card)).toBe(false);
        });
    });

    // -------------------------------------------------------------------------
    // 2. displayStock getter tests
    // -------------------------------------------------------------------------
    describe("ProductCard.displayStock", () => {
        const getDisplayStock = (card) => {
            const getter = Object.getOwnPropertyDescriptor(
                ProductCard.prototype,
                "displayStock"
            ).get;
            return getter.call(card);
        };

        test("returns false when displayStockAlert is true", () => {
            const card = {
                get displayStockAlert() {
                    return true;
                },
            };
            expect(getDisplayStock(card)).toBe(false);
        });

        test("returns super value or true when displayStockAlert is false", () => {
            const card = {
                get displayStockAlert() {
                    return false;
                },
            };
            expect(getDisplayStock(card)).toBe(true);
        });
    });

    // -------------------------------------------------------------------------
    // 3. productStockQty getter tests
    // -------------------------------------------------------------------------
    describe("ProductCard.productStockQty", () => {
        const getProductStockQty = (card) => {
            const getter = Object.getOwnPropertyDescriptor(
                ProductCard.prototype,
                "productStockQty"
            ).get;
            return getter.call(card);
        };

        test("returns 0 when props.product is null or undefined", () => {
            expect(getProductStockQty({ props: {} })).toBe(0);
            expect(getProductStockQty({ props: { product: null } })).toBe(0);
        });

        test("parses integer alert_tag correctly", () => {
            const card = {
                props: {
                    product: { id: 1, alert_tag: "8" },
                },
            };
            expect(getProductStockQty(card)).toBe(8);
        });

        test("parses float alert_tag preserving decimal values", () => {
            const card = {
                props: {
                    product: { id: 1, alert_tag: "4.5" },
                },
            };
            expect(getProductStockQty(card)).toBe(4.5);
        });

        test("delegates to pos.getProductStockQty when alert_tag is not provided", () => {
            const product = { id: 10, name: "Juice" };
            const card = {
                props: { product },
                pos: {
                    getProductStockQty: (p) => (p.id === 10 ? 12 : 0),
                },
            };
            expect(getProductStockQty(card)).toBe(12);
        });

        test("falls back to product.qty_available when pos.getProductStockQty is unavailable", () => {
            const card = {
                props: {
                    product: { id: 11, qty_available: 7 },
                },
                pos: null,
            };
            expect(getProductStockQty(card)).toBe(7);
        });

        test("handles string quantity in qty_available", () => {
            const card = {
                props: {
                    product: { id: 12, qty_available: "15.0" },
                },
                pos: null,
            };
            expect(getProductStockQty(card)).toBe(15);
        });

        test("returns 0 when no quantity is available", () => {
            const card = {
                props: {
                    product: { id: 13 },
                },
                pos: null,
            };
            expect(getProductStockQty(card)).toBe(0);
        });
    });
});
