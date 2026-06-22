/** @odoo-module **/

QUnit.test("show warning when start date is greater", async function(assert) {
    const dashboard = new DashboardFleetRental();

    dashboard.modal_warning = {
        el: {
            style: {}
        }
    };
    dashboard.start_date = {
        el: {
            value: "2026-05-20"
        }
    };
    dashboard.end_date = {
        el: {
            value: "2026-05-10"
        }
    };

    const result = dashboard.onApplyFilter();

    assert.strictEqual(result, false);
    assert.strictEqual(
        dashboard.modal_warning.el.style.display,
        "block"
    );
});

QUnit.test("close modal hides warning", function(assert){

    const dashboard = new DashboardFleetRental();

    dashboard.modal_warning = {
        el: {
            style: {
                display: "block"
            }
        }
    };

    dashboard.closeModal();

    assert.strictEqual(
        dashboard.modal_warning.el.style.display,
        "none"
    );
});
