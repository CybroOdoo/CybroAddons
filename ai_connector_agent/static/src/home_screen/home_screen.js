/** @odoo-module **/
import { registry } from "@web/core/registry";
import { Component, useState, onWillStart, useEffect } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class AiChatterHome extends Component {
    setup() {
        this.actionService = useService("action");
        this.orm = useService("orm");
        this.rpc = useService("rpc");
        this.state = useState({
            aiAgents: [],
            selectedAgent: null,   // id or null
            aiModels: [],
            loadingModels: false,
            selectedModel: null,
        });

        // Load agents (and be sure to fetch ai_model_ids)
        onWillStart(async () => {
            this.state.aiAgents = await this.orm.searchRead(
                "ai.providers",
                [["ai_model_ids", "!=", false]],
                ["id", "name", "ai_model_ids"]
            );

            // Auto-redirect if preference exists and not explicitly skipped
            const context = this.props.action?.context || {};
            if (!context.skip_redirect) {
                const activeConfig = await this.rpc("/ai_chat/get_active_provider");
                if (activeConfig.success && activeConfig.agent_id && activeConfig.model_id) {
                    this.state.selectedAgent = activeConfig.agent_id;
                    this.state.selectedModel = activeConfig.model_id;
                    // Need to load models for the redirect logic to have names
                    await this.getAiModels(this.state.selectedAgent);
                    this.startChat();
                }
            }
        });

        // React when selectedAgent changes
        useEffect(
            () => {
                if (!this.state.selectedAgent) {
                    this.state.aiModels = [];
                    this.state.selectedModel = null;
                    return;
                }
                this.getAiModels(this.state.selectedAgent);
                this.saveActiveConfig();
            },
            () => [this.state.selectedAgent]
        );

        // React when selectedModel changes
        useEffect(
            () => {
                this.saveActiveConfig();
            },
            () => [this.state.selectedModel]
        );
    }

    async saveActiveConfig() {
        if (this.state.selectedAgent || this.state.selectedModel) {
            try {
                await this.rpc("/ai_chat/save_active_config", {
                    ai_agent_id: this.state.selectedAgent,
                    ai_model_id: this.state.selectedModel,
                });
            } catch (e) {
                console.error("Failed to save active config:", e);
            }
        }
    }

    async startChat() {
        if (!this.state.selectedAgent || !this.state.selectedModel) {
            console.warn("Please select both AI Agent and Model");
            return;
        }

        const selectedAgentData = this.state.aiAgents.find(
            agent => agent.id == this.state.selectedAgent
        );
        const selectedModelData = this.state.aiModels.find(
            model => model.id == this.state.selectedModel
        );

        return this.actionService.doAction({
            target: "current",
            tag: "ai_chatter_screen",
            type: "ir.actions.client",
            context: {
                ai_agent_id: this.state.selectedAgent,
                ai_model_id: this.state.selectedModel,
                ai_agent_name: selectedAgentData?.name,
                ai_model_name: selectedModelData?.modelId || selectedModelData?.name,
            }
        });
    }

    async getAiModels(selectedAgent) {
        // Normalize id type (string vs number)
        const selectedId = typeof selectedAgent === "string" ? parseInt(selectedAgent) : selectedAgent;

        const agent = this.state.aiAgents.find((a) => a.id === selectedId);
        if (!agent) {
            this.state.aiModels = [];
            return;
        }

        // ai_model_ids should be an array of ids (handle [id, name] just in case)
        const raw = agent.ai_model_ids || [];
        const modelIds = Array.isArray(raw) ? raw.map((v) => (Array.isArray(v) ? v[0] : v)) : [];

        if (!modelIds.length) {
            this.state.aiModels = [];
            return;
        }

        this.state.loadingModels = true;
        try {
            this.state.aiModels = await this.orm.searchRead(
                "ai.model",
                [["id", "in", modelIds]],
                ["id", "modelId"] // Include all necessary fields
            );
        } finally {
            this.state.loadingModels = false;
        }
    }

}

AiChatterHome.template = "ai_connector_agent.ai_chatter_home";
registry.category("actions").add("ai_chatter_home", AiChatterHome);
