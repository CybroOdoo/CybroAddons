import { expect, test } from "@odoo/hoot";
import { mountWithCleanup, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";

definePosModels();

test("Navbar shows countdown timer when pos_lock is enabled", async () => {
    const store = await setupPosEnv();
    store.config.pos_lock = true;
    store.config.idle_time_limit = 10;

    const navbar = await mountWithCleanup(Navbar);
    expect(navbar.timerState.time).not.toBe(null);
    expect(".pos-timer").toHaveCount(1);
});

test("Navbar hides countdown timer when pos_lock is disabled", async () => {
    const store = await setupPosEnv();
    store.config.pos_lock = false;
    store.config.idle_time_limit = 10;

    const navbar = await mountWithCleanup(Navbar);
    expect(navbar.timerState.time).toBe(null);
    expect(".pos-timer").toHaveCount(0);
});

test("Navbar resets countdown timer on user activity", async () => {
    const store = await setupPosEnv();
    store.config.pos_lock = true;
    store.config.idle_time_limit = 5;

    const navbar = await mountWithCleanup(Navbar);
    const initialDeadline = navbar.idleDeadline;
    expect(initialDeadline).toBeGreaterThan(0);

    navbar.idleDeadline -= 30000;
    navbar.onUserActivity();
    expect(navbar.idleDeadline >= initialDeadline).toBe(true);
});

test("Navbar tickTimer locks session when idle deadline expires", async () => {
    const store = await setupPosEnv();
    store.config.pos_lock = true;
    store.config.idle_time_limit = 5;

    const navbar = await mountWithCleanup(Navbar);

    let sessionLocked = false;
    navbar.lockSession = () => {
        sessionLocked = true;
    };

    navbar.idleDeadline = Date.now() - 1000;
    navbar.tickTimer();

    expect(navbar.timerState.time).toBe("0 m 0 s");
    expect(sessionLocked).toBe(true);
});

test("Navbar stopIdleTimer clears the active interval", async () => {
    const store = await setupPosEnv();
    store.config.pos_lock = true;
    store.config.idle_time_limit = 10;

    const navbar = await mountWithCleanup(Navbar);
    expect(navbar.idleIntervalId).not.toBe(null);

    navbar.stopIdleTimer();
    expect(navbar.idleIntervalId).toBe(null);
});
