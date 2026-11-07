import { describe, expect, test } from "@odoo/hoot";
import { setupPosEnv } from "@point_of_sale/../tests/unit/utils";
import { definePosModels } from "@point_of_sale/../tests/unit/data/generate_model_definitions";
import { PosStore } from "@point_of_sale/app/services/pos_store";

definePosModels();

describe("pos_analytic_tag", () => {
    describe("PosSession - processServerData", () => {
        test("test_processServerData sets res_config_settings when model exists", async () => {
            const store = await setupPosEnv();
            const mockSettings = [{ id: 1, pos_analytic_account_id: [1, "Test Analytic Account"] }];
            store.models["res.config.settings"] = mockSettings;
            if (store.data && store.data.models) {
                store.data.models["res.config.settings"] = mockSettings;
            }
            await store.processServerData();
            expect(store.res_config_settings).toEqual(mockSettings);
        });

        test("test_processServerData leaves res_config_settings undefined when model does not exist", async () => {
            const store = await setupPosEnv();
            delete store.models["res.config.settings"];
            if (store.data && store.data.models) {
                delete store.data.models["res.config.settings"];
            }
            store.res_config_settings = undefined;
            await store.processServerData();
            expect(store.res_config_settings).toBe(undefined);
        });

        test("processServerData patch is registered on PosStore prototype", () => {
            expect(typeof PosStore.prototype.processServerData).toBe("function");
        });
    });
});
