/** @odoo-module **/

export class LoopManager {
    constructor(builder) {
        this.builder = builder;
    }

    getDefaultLoopConfig() {
        return {
            loopType: "foreach",
            collectionPath: "",
            maxIterations: 1,
            condition: ""
        };
    }


    /** Required by NodeManager */
    getLoopStatus(nodeId) {
        const config = this.builder.state.nodeConfigs[nodeId]?.config;
        if (!config) return "Incomplete";

        const type = config.loopType || "foreach";

        if (type === "foreach") {
            return config.collectionPath
                ? `Iterate: ${config.collectionPath}`
                : "Select array path";
        }

        return "Unknown Loop Type";
    }

    /** Required by NodeManager */
    validateLoopConfig(nodeId) {
        const config = this.builder.state.nodeConfigs[nodeId]?.config;
        if (!config) return false;

        const type = config.loopType || "foreach";

        if (type === "foreach") {
            const isValid = !!config.collectionPath && config.collectionPath.trim() !== "";
            return isValid;
        }

        return false;
    }
}