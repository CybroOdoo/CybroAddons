/** @odoo-module **/

import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { defineModels, models, mountWithCleanup, onRpc } from "@web/../tests/web_test_helpers";
import { AccountDashboard } from "@odoo_accounting_dashboard/js/accounting_dashboard";

// Mock window.Chart if not defined in headless testing environment
if (typeof window !== "undefined" && !window.Chart) {
    window.Chart = class MockChart {
        constructor(canvas, config) {
            this.canvas = canvas;
            this.config = config;
        }
        destroy() {}
        static getChart() {
            return null;
        }
    };
}

class AccountMove extends models.Model {
    _name = "account.move";
}

defineMailModels();
defineModels([AccountMove]);

describe("AccountDashboard Component Tests", () => {
    function setupMockRpc() {
        onRpc("account.move", "get_datas", () => ({
            open_invoice: 7,
            paid_invoice: 15,
            income: "25000.00",
            currency_symbol: "$",
            unreconcile_items: [4],
            journal_data: [
                { id: 1, name: "Customer Invoices", type: "sale" },
                { id: 2, name: "Vendor Bills", type: "purchase" },
            ],
        }));

        onRpc("account.move", "get_income_chart", () => ({
            income: [1000, 2000, 3000],
            expense: [500, 800, 1200],
            date: [1, 2, 3],
            profit: [500, 1200, 1800],
        }));

        onRpc("account.move", "get_payment_data", () => [
            { id: 101, partner: "Acme Corp", amount: 1500.0, date: "2026-11-01" },
            { id: 102, partner: "Globex Inc", amount: 2300.0, date: "2026-11-02" },
        ]);

        onRpc("account.move", "get_top_datas", () => ({
            top_customers: [
                { id: 1, name: "Top Customer Alpha", amount: 12000.0 },
                { id: 2, name: "Top Customer Beta", amount: 8500.0 },
            ],
            top_vendors: [
                { id: 3, name: "Top Vendor Gamma", amount: 6200.0 },
            ],
        }));

        onRpc("account.move", "get_aged_payable", () => ({
            partner: ["Acme Corp", "Globex Inc"],
            amount: [1200.0, 800.0],
        }));

        onRpc("account.move", "get_sale_revenue", () => [
            { customer_id: 1, customer: "Top Revenue Customer", total_amount: 15400.0 },
        ]);

        onRpc("account.move", "get_bank_balance", () => [
            { id: 1, name: "Bank Account 1", balance: 45000.0 },
            { id: 2, name: "Cash Account", balance: 2500.0 },
        ]);
    }

    beforeEach(() => {
        setupMockRpc();
    });

    test("AccountDashboard mounts and renders all dashboard tiles correctly", async () => {
        const comp = await mountWithCleanup(AccountDashboard);

        // Verify Open Invoice tile count and state properties
        expect(".accounts-dashboard-wrap").toHaveCount(1);
        expect(comp.state.data.open_invoice).toBe(7);
        expect(comp.state.data.paid_invoice).toBe(15);
        expect(comp.state.data.income).toBe("25000.00");
        expect(comp.state.data.currency_symbol).toBe("$");
        expect(comp.state.data.unreconcile_items).toEqual([4]);
    });

    test("AccountDashboard renders payment lists and bank balances correctly", async () => {
        const comp = await mountWithCleanup(AccountDashboard);

        expect(comp.state.payment_data).toHaveLength(2);
        expect(comp.state.payment_data[0].partner).toBe("Acme Corp");
        expect(comp.state.payment_data[1].partner).toBe("Globex Inc");

        expect(comp.state.balance).toHaveLength(2);
        expect(comp.state.balance[0].name).toBe("Bank Account 1");
        expect(comp.state.balance[0].balance).toBe(45000.0);
    });

    test("AccountDashboard renders top sale revenue and top customer/vendor data", async () => {
        const comp = await mountWithCleanup(AccountDashboard);

        expect(comp.state.top_sale_cust).toHaveLength(1);
        expect(comp.state.top_sale_cust[0].customer).toBe("Top Revenue Customer");
        expect(comp.state.top_sale_cust[0].total_amount).toBe(15400.0);

        expect(comp.state.top.top_customers).toHaveLength(2);
        expect(comp.state.top.top_customers[0].name).toBe("Top Customer Alpha");
        expect(comp.state.top.top_vendors).toHaveLength(1);
        expect(comp.state.top.top_vendors[0].name).toBe("Top Vendor Gamma");
    });

    test("AccountDashboard filter changes update state and trigger data re-fetch", async () => {
        let incomeChartCallCount = 0;
        onRpc("account.move", "get_income_chart", () => {
            incomeChartCallCount++;
            return {
                income: [100],
                expense: [50],
                date: [1],
                profit: [50],
            };
        });

        const comp = await mountWithCleanup(AccountDashboard);
        const initialCount = incomeChartCallCount;

        // Change Income/Expense filter
        await comp.onIncomeExpenseChange({ target: { value: "expense" } });
        expect(comp.state.IncomeExpense).toBe("expense");
        expect(incomeChartCallCount).toBeGreaterThan(initialCount);

        // Change Income Period filter
        await comp.onIncomePeriodChange({ target: { value: "income_this_year" } });
        expect(comp.state.income).toBe("income_this_year");

        // Change Payment List filter
        await comp.onPaymentListFilterChange({ target: { value: "vendor_payment" } });
        expect(comp.state.payment_list_filter).toBe("vendor_payment");

        // Change Payment Data filter
        await comp.onPaymentDataFilterChange({ target: { value: "this_year" } });
        expect(comp.state.payment_data_filter).toBe("this_year");

        // Change Aged filter
        await comp.onAgedFilterChange({ target: { value: "aged_payable" } });
        expect(comp.state.aged_filter).toBe("aged_payable");

        // Change Top filter
        await comp.onTopFilterChange({ target: { value: "this_year" } });
        expect(comp.state.top_filter).toBe("this_year");
    });
});
