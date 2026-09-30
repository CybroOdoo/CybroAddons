/** @odoo-module **/

import { Component, useState, onMounted, useRef, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { session } from "@web/session";
import { NodeManager } from "./node_manager";
import { ConnectionManager } from "./connection_manager";
import { WorkflowIO } from "./workflow_io";
import { NodeTemplates } from "./node_templates";
import { FormManager } from "./form_manager";
import { LoopManager } from "./loop_manager";

function generateUUID() {
    return 'node-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
}


class WorkflowBuilder extends Component {

    static props = {
        action: { type: Object, optional: true },
        actionId: { type: Number, optional: true },
        updateActionState: { type: Function, optional: true },
        className: { type: String, optional: true },
    };


    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.canvasRef = useRef("canvas");
        this.configPanelRef = useRef("config-panel");
        this.isDirty = false;
        this.lastSavedAt = null;
        this.markDirty = () => {
            this.isDirty = true;
            this.updateSaveButtonUI?.();
            if (this.queueDraftSave) this.queueDraftSave();
        };
        this.updateSaveButtonUI = () => {
            const btn = document.querySelector('#workflow-save-btn');
            if (!btn) return;
            btn.innerText = this.isDirty ? 'Save*' : 'Save';
            const stamp = document.querySelector('#workflow-save-stamp');
            if (stamp) stamp.innerText = this.lastSavedAt ? `Saved ${this.lastSavedAt}` : '';
        };
        this.canvasWrapperRef = useRef("canvasWrapper");
        this.isPanning = false;
        this.panStartX = 0;
        this.panStartY = 0;
        this.scrollStartX = 0;
        this.scrollStartY = 0;
        this.state = useState({
            workflowNodes: [],
            nodeIdCounter: 0,
            nodeConfigs: {},
            selectedNode: null,
            showInstructions: true,
            connections: [],
            tempConnection: null,
            configUpdateCounter: 0,
            workflowId: this.props?.action?.params?.workflow_id || null,
            workflowName: this.props?.action?.params?.workflow_name || null,
            nodeResponses: {},
            workflowTestResults: null,
            lastTestTimestamp: null,
            nodeIdMap: {},
            fixedNodes: {},
            availableModels: [],
            filteredModels: [],
            isModelListOpen: false,
            availableFields: [],
            filteredFields: [],
            isFieldListOpen: false,
            ormAdvancedMode: false,
            zoomLevel: 1.0,
            leftPanelWidth: 280,
            rightPanelWidth: 380,
            isResizing: false,
            leftPanelOpen: true,
            rightPanelOpen: true,
            rightPanelMode: 'node',
            workflowSettings: {
                trigger_type: 'manual',
                interval_number: 1,
                interval_type: 'hours',
                trigger_model: '',
                trigger_on: 'on_create',
                cron_active: false
            },

        });

        this.state.uiPrefs = this.state.uiPrefs || {};
        this.state.uiPrefs.edgeMode = this.state.uiPrefs.edgeMode || 'route_until_error';

        this.loopManager = new LoopManager(this);
        this.nodeManager = new NodeManager(this);
        this.connectionManager = new ConnectionManager(this);
        this.workflowIO = new WorkflowIO(this);
        this.nodeTemplates = new NodeTemplates(this);
        this.formManager = new FormManager(this);
        this.history = {
            past: [],
            future: []
        };


        this.generateUUID = generateUUID;
        onWillStart(async () => {
            try {
                const result = await this.orm.call('api.workflow', 'get_existing_models', []);

                if (Array.isArray(result)) {
                    this.state.availableModels = result;
                    this.state.filteredModels = result.slice(0, 20);
                } else {
                    this.state.availableModels = [];
                    this.state.filteredModels = [];
                }
            } catch (e) {
                console.error("❌ Failed to load models", e);
            }
        });

        onMounted(() => {

            this.connectionManager.setupConnections();
            this.setupConfigEventHandlers();

            document.addEventListener('keydown', this.handleGlobalKeyDown.bind(this));

            if (this.canvasRef.el) {
                this.canvasRef.el.addEventListener('click', (e) => {
                    if (e.target === this.canvasRef.el || e.target.classList.contains('workflow-canvas')) {
                        if (this.connectionManager && this.connectionManager.selectedConnectionId) {
                            this.connectionManager.selectedConnectionId = null;
                            this.connectionManager.updateConnections(); // Remove blue highlight
                        }
                    }
                });
            }

            // C. Load Workflow Data
            this.loadWorkflowFromParams();

            // D. Load Drafts (Autosave Recovery)
            this.workflowIO.loadAutosaveDraft().then((serverDraft) => {
                if (!serverDraft) this.tryRestoreDraft();
                setTimeout(() => this.setupFixedNodes(), 60);
            }).catch(() => {
                this.tryRestoreDraft();
                setTimeout(() => this.setupFixedNodes(), 60);
            });

            // E. Initialize Response Data System
            this.initializeResponseDataSystem();

            // F. Define Autosave Logic
            this._autoSaveHandler = async (isUnloading = false) => {
                try {
                    const payloadObj = this.workflowIO.serializeForSave();
                    if (isUnloading) {
                        // Special logic for closing tab
                        const jsonRpcPayload = {
                            jsonrpc: "2.0", method: "call", id: Math.floor(Math.random() * 1000000),
                            params: { workflow_data: payloadObj }
                        };
                        fetch('/api/workflows/autosave', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json', 'X-Openerp-Session-Id': odoo.csrf_token },
                            body: JSON.stringify(jsonRpcPayload),
                            keepalive: true
                        }).catch(console.error);
                    } else {
                        // Normal Autosave
                        await this.rpc('/api/workflows/autosave', { workflow_data: payloadObj });
                    }
                    if (this.saveDraftNow) this.saveDraftNow();
                } catch (e) {
                    console.warn("Autosave failed:", e);
                }
            };

            // G. Autosave Listeners
            this._beforeUnload = () => {
                this._autoSaveHandler(true);
            };
            window.addEventListener('beforeunload', this._beforeUnload);
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'hidden') this._autoSaveHandler(true);
            });
            setTimeout(() => this.resetViewPosition(), 500);
        });


        this.onWillUnmount = () => {
            window.removeEventListener('beforeunload', this._beforeUnload);
            // don’t clear here; the draft is useful on refresh/navigation
        };
    }

    openSettings() {

        // 1. Deselect any active node (so we don't see node settings)
        this.deselectAllNodes();

        // 2. Switch mode
        this.state.rightPanelMode = 'settings';

        // 3. Force open the panel if it was closed
        this.state.rightPanelOpen = true;
    }

    onModelSearchInput(ev) {
        const query = ev.target.value.toLowerCase();
        const value = ev.target.value;

        if (this.state.rightPanelMode === 'settings') {
            this.updateWorkflowSetting('trigger_model', value);
        } else if (this.state.selectedNode) {
            this.updateNodeConfig(this.state.selectedNode, 'model', value);
        }

        // Filter the list based on Technical Name OR Human Name
        if (!query) {
            this.state.filteredModels = this.state.availableModels.slice(0, 20);
        } else {
            this.state.filteredModels = this.state.availableModels.filter(m =>
                m.model.toLowerCase().includes(query) ||
                m.name.toLowerCase().includes(query)
            ).slice(0, 20); // Always limit results to prevent lag
        }

        this.state.isModelListOpen = true;
    }

    // 🆕 2. Handle Clicking a Dropdown Item
    selectModel(modelTechnicalName) {
        if (this.state.rightPanelMode === 'settings') {
            this.updateWorkflowSetting('trigger_model', modelTechnicalName);
        } else if (this.state.selectedNode) {
            this.updateNodeConfig(this.state.selectedNode, 'model', modelTechnicalName);
        }

        // Hide Dropdown
        this.state.isModelListOpen = false;
    }

    // 🆕 3. Handle Automation Settings Updates
    updateWorkflowSetting(key, value) {
        this.state.workflowSettings[key] = value;
        this.markDirty();
        this.queueDraftSave();
    }

    onModelInputFocus() {
        this.state.isModelListOpen = true;

        // FIX: Always reset list if the input is effectively empty
        let currentModel = '';
        if (this.state.rightPanelMode === 'settings') {
            currentModel = this.state.workflowSettings.trigger_model;
        } else if (this.state.selectedNode) {
            currentModel = this.state.nodeConfigs[this.state.selectedNode]?.config?.model;
        }

        // If current model is empty, OR if we have no filtered results yet
        if (!currentModel || this.state.filteredModels.length === 0) {
            this.state.filteredModels = this.state.availableModels.slice(0, 20);
        }
    }

    onModelInputBlur() {
        // Small delay is needed so the "Click" event on the item registers
        // before the list disappears
        setTimeout(() => {
            this.state.isModelListOpen = false;
        }, 200);
    }


    async onFieldInputFocus() {
        const nodeId = this.state.selectedNode;
        if (!nodeId || !this.state.nodeConfigs[nodeId]) return;

        // FIX: Access config from state, not props
        const modelName = this.state.nodeConfigs[nodeId].config.model;

        if (!modelName) {
            this.state.availableFields = [];
            this.state.filteredFields = [];
            return;
        }

        // Only fetch if we haven't fetched for this model yet (optional optimization)
        try {
            const fields = await this.orm.call('api.workflow', 'get_model_fields', [modelName]);

            // Safety check
            if (Array.isArray(fields)) {
                this.state.availableFields = fields;
                this.state.filteredFields = fields;
                this.state.isFieldListOpen = true;
            } else {
                console.warn("get_model_fields returned non-array:", fields);
                this.state.availableFields = [];
            }
        } catch (error) {
            console.error("Error fetching fields:", error);
            this.notification.add("Failed to fetch fields: " + error.message, { type: 'danger' });
        }
    }


    onFieldInput(ev) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const inputVal = ev.target.value;
        this.updateNodeConfig(nodeId, 'fields', inputVal); // Update the actual config

        // Logic to filter the dropdown based on the *last* typed word
        // e.g. if input is "name, ema", we filter for "ema"
        const terms = inputVal.split(',').map(t => t.trim());
        const currentSearch = terms[terms.length - 1].toLowerCase();

        if (this.state.availableFields) {
            if (currentSearch) {
                this.state.filteredFields = this.state.availableFields.filter(f =>
                    f.name.toLowerCase().includes(currentSearch) ||
                    f.string.toLowerCase().includes(currentSearch)
                );
            } else {
                this.state.filteredFields = this.state.availableFields;
            }
        }

        this.state.isFieldListOpen = true;
    }


    onFieldInputBlur() {
        setTimeout(() => {
            this.state.isFieldListOpen = false;
        }, 200);
    }


    getSelectedNodeTestResult() {
        if (!this.state.selectedNode || !this.state.nodeTestResults) {
            return null;
        }
        return this.state.nodeTestResults[this.state.selectedNode];
    }

    getConditionResult(nodeId) {
        return this.state.conditionResults ? this.state.conditionResults[nodeId] : null;
    }

    async runWorkflowTest() {
        try {
            this.notification.add("Running workflow test...", { type: 'info' });

            this.state.workflowTestResults = null;
            this.state.nodeTestResults = null;
            this.state.configUpdateCounter++;

            const result = await this.workflowIO.testWorkflow();

            if (result && result.success) {
                this.state.workflowTestResults = result;
                this.state.lastTestTimestamp = new Date().toISOString();

                if (result.results && Array.isArray(result.results)) {
                    this.state.nodeTestResults = {};
                    result.results.forEach(nodeResult => {
                        this.state.nodeTestResults[nodeResult.node_id] = nodeResult;
                    });
                    requestAnimationFrame(() => this.connectionManager.updateConnections());
                    this.connectionManager.updateConnections();
                }

                setTimeout(() => {
                    this.refreshAllResponseFields();
                }, 500);

                this.state.configUpdateCounter++;
                this.connectionManager.updateConnections();

                const successMsg = result.message || "Workflow test completed successfully!";
                this.notification.add(`✅ ${successMsg}`, {
                    type: 'success',
                });

                setTimeout(() => {
                    this.setupConfigEventHandlers();
                    this.refreshAllNodeStatuses();
                }, 1000);
                window.requestAnimationFrame(() => {
                    if (this.connectionManager) {
                        this.connectionManager.updateConnections();
                    }
                });
            } else {
                this.notification.add(`❌ Workflow test failed: ${result?.error || 'Unknown error'}`, {
                    type: 'danger'
                });
            }

            return result;
        } catch (error) {
            console.error('Workflow test error:', error);
            this.notification.add(`❌ Workflow test failed: ${error.message}`, {
                type: 'danger'
            });
            throw error;
        }
    }

    get draftKey() {
        const db = session.db || 'default';
        return this.state.workflowId ? `wb_draft_${db}_${this.state.workflowId}` : `wb_draft_${db}_new`;
    }

    serializeDraft() {
        return {
            db: session.db || 'default',
            workflowId: this.state.workflowId,
            workflowName: this.state.workflowName,
            nodes: Object.values(this.state.nodeConfigs).map(n => ({
                id: n.id, type: n.type, x: n.x, y: n.y, config: n.config
            })),
            connections: this.state.connections.slice(),
            metadata: { savedAt: new Date().toISOString() }
        };
    }

    saveDraftNow() {
        if (!this.draftKey) return;
        try {
            const draft = this.serializeDraft();
            localStorage.setItem(this.draftKey, JSON.stringify(draft));
        } catch (e) {
            console.error("Draft save failed:", e);
        }
    }

    queueDraftSave = (() => {
        let t = null;
        return () => {
            clearTimeout(t);
            t = setTimeout(() => this.saveDraftNow(), 300);
        };
    })();

    startResize(side, ev) {
        ev.preventDefault();
        this.resizingSide = side; // 'left' or 'right'
        this.resizeStartX = ev.clientX;
        this.resizeStartWidth = side === 'left' ? this.state.leftPanelWidth : this.state.rightPanelWidth;
        this.state.isResizing = true;

        this.boundHandleResizeMove = this.handleResizeMove.bind(this);
        this.boundHandleResizeUp = this.handleResizeUp.bind(this);

        document.addEventListener('mousemove', this.boundHandleResizeMove);
        document.addEventListener('mouseup', this.boundHandleResizeUp);

        document.body.style.cursor = 'col-resize';
        document.body.classList.add('resizing-mode');
    }

    handleResizeMove(ev) {
        if (!this.state.isResizing) return;

        requestAnimationFrame(() => {
            const dx = ev.clientX - this.resizeStartX;

            if (this.resizingSide === 'left') {
                const newWidth = Math.max(200, Math.min(600, this.resizeStartWidth + dx));
                this.state.leftPanelWidth = newWidth;
            } else {
                const newWidth = Math.max(250, Math.min(800, this.resizeStartWidth - dx));
                this.state.rightPanelWidth = newWidth;
            }
        });
    }

    handleResizeUp() {
        this.state.isResizing = false;
        this.resizingSide = null;

        document.removeEventListener('mousemove', this.boundHandleResizeMove);
        document.removeEventListener('mouseup', this.boundHandleResizeUp);

        document.body.style.cursor = '';
        document.body.classList.remove('resizing-mode');

    }


    clearDraft() {
        if (!this.draftKey) return;
        try {
            localStorage.removeItem(this.draftKey);
        } catch (_) {
        }
    }

    tryRestoreDraft() {
        if (!this.draftKey) return false;

        const raw = localStorage.getItem(this.draftKey);
        if (!raw) return false;

        try {
            const draft = JSON.parse(raw);

            const currentDb = session.db || 'default';
            if (draft.db && draft.db !== currentDb) {
                localStorage.removeItem(this.draftKey);
                return false;
            }

            const currentId = this.state.workflowId || null;
            const draftId = draft.workflowId || null;

            if ((draftId === currentId) || (!draftId && !currentId)) {

                if (Array.isArray(draft.nodes)) {
                    // 2. Use RAF to prevent 'insertBefore' DOM crashes
                    window.requestAnimationFrame(() => {
                        this.workflowIO.loadWorkflowData({
                            nodes: draft.nodes,
                            connections: draft.connections || []
                        });

                        // 3. Chain the next updates so they happen AFTER nodes exist
                        window.requestAnimationFrame(() => {
                            if (this.connectionManager) {
                                this.connectionManager.updateConnections();
                            }
                            // 4. CRITICAL FIX: Run this HERE, not in a parallel timeout
                            // This ensures we don't create duplicate 'Start' nodes
                            this.setupFixedNodes();
                        });
                    });

                    this.state.showInstructions = false;
                    this.notification.add("Restored unsaved draft", { type: 'info' });
                    return true;
                }
            }
        } catch (e) {
            console.warn("Failed to parse draft:", e);
        }
        return false;
    }


    getNodeResponseData(nodeId) {
        return this.workflowIO.getNodeResponseData(nodeId);
    }


    clearWorkflowTestResults() {
        this.state.workflowTestResults = null;
        this.state.nodeTestResults = null;
        this.state.lastTestTimestamp = null;
        this.state.configUpdateCounter++;
    }

    getNodeExecutionPath(nodeId) {
        const flowResults = this.getFlowResults();
        for (const flow of flowResults) {
            if (flow.executed_nodes && flow.executed_nodes.includes(nodeId)) {
                return {
                    flowIndex: flowResults.indexOf(flow) + 1,
                    path: flow.path,
                    success: flow.success
                };
            }
        }
        return null;
    }

    setupConfigPanelEvents() {
        this.setupConfigEventHandlers();
    }

    getNodeId(originalId = null) {
        if (originalId && this.state.nodeIdMap[originalId]) {
            return this.state.nodeIdMap[originalId];
        }
        const newId = this.generateUUID();
        if (originalId) {
            this.state.nodeIdMap[originalId] = newId;
        }
        return newId;
    }


    rebuildNodeMapping(nodes) {
        nodes.forEach(node => {
            if (node.id && !this.state.nodeIdMap[node.id]) {
                this.state.nodeIdMap[node.id] = this.generateUUID();
            }
        });
    }

    resolveConnectionIds(connections) {
        return connections.map(conn => ({
            ...conn,
            source: this.state.nodeIdMap[conn.source] || conn.source,
            target: this.state.nodeIdMap[conn.target] || conn.target
        }));
    }


    loadWorkflowFromParams() {
        const params = this.props?.action?.params;

        if (params?.workflow_data && typeof params.workflow_data === 'object' && Object.keys(params.workflow_data).length > 0) {
            if (this.isValidWorkflowData(params.workflow_data)) {
                setTimeout(() => {
                    this.workflowIO.loadWorkflowData(params.workflow_data);
                    this.workflowIO.importWorkflowData(params.workflow_data);
                    this.state.showInstructions = false;
                }, 100);
            } else {
                this.notification.add("Invalid workflow data format", { type: 'warning' });
            }
        }
    }

    isValidWorkflowData(data) {
        return data && typeof data === 'object' && Array.isArray(data.nodes);
    }


    onDragStart(ev) {
        // 1. Get the type from the HTML data-type attribute
        const type = ev.target.dataset.type;

        if (type) {
            // 2. Set the data so 'onDrop' can read it
            ev.dataTransfer.setData('text/plain', type);
            ev.dataTransfer.dropEffect = 'copy';
        }
    }

    setupConfigEventHandlers() {
        setTimeout(() => {
            const configPanel = this.configPanelRef.el;
            if (!configPanel) {
                console.warn("Config panel not ready");
                return;
            }

            // DO NOT replace configPanel.innerHTML
            // Only attach handlers to existing DOM

            this.setupInputHandlers(configPanel);
            this.setupSelectHandlers(configPanel);
            this.setupTextareaHandlers(configPanel);
            this.setupButtonHandlers(configPanel);
            this.setupConditionalNodeHandlers(configPanel);

            // ✅ Initialize Loop UI if selected
            const nodeId = this.state.selectedNode;
            // if (nodeId && this.state.nodeConfigs[nodeId]?.type === "loop") {
            //     this.loopManager.setupLoopUI(configPanel, nodeId);
            // }

            this.refreshConfigPanelFields();
        }, 50);
    }


    setupConditionalNodeHandlers(container) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;
        const nodeType = this.state.nodeConfigs[nodeId]?.type;

        if (nodeType !== "condition") {
            return;
        }


        // 1. Fix Source Data Selects
        const sourceDataSelects = container.querySelectorAll('select[data-config-key="sourceData"]');
        sourceDataSelects.forEach(select => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (select.dataset.condHandlerAttached === 'true') return;
            select.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            select.addEventListener('change', (e) => {
                this.handleSourceDataChange(nodeId, e.target.value);
                setTimeout(() => {
                    this.setupConfigEventHandlers();
                }, 100);
            });
        });

        // 2. Fix Previous Node Selects (THIS IS THE ONE CAUSING YOUR ISSUE)
        const previousNodeSelects = container.querySelectorAll('.previous-node-select');
        previousNodeSelects.forEach(select => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (select.dataset.condHandlerAttached === 'true') return;
            select.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            select.addEventListener('change', (e) => {
                this.handlePreviousNodeChange(nodeId, e.target.value);
                setTimeout(() => {
                    this.populateLeftOperandDropdown(nodeId, container);
                }, 150);
            });
        });

        // 3. Fix Left Operand Selects
        const leftOperandSelects = container.querySelectorAll('.response-field-dropdown, select[data-action="leftOperandSelect"]');
        leftOperandSelects.forEach(select => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (select.dataset.condHandlerAttached === 'true') return;
            select.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            select.addEventListener('change', (e) => {
                this.handleLeftOperandFieldSelect(nodeId, e.target.value);
            });
        });

        // Populate dropdown (This is safe to call multiple times as it clears innerHTML)
        this.populateLeftOperandDropdown(nodeId, container);

        // 4. Fix Manual Path Inputs
        const manualPathInputs = container.querySelectorAll('.manual-json-path');
        manualPathInputs.forEach(input => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (input.dataset.condHandlerAttached === 'true') return;
            input.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            input.addEventListener('input', (e) => {
                this.handleManualDataPathInput(nodeId, e.target.value);
            });
            input.addEventListener('blur', (e) => {
                this.handleManualDataPathInput(nodeId, e.target.value);
            });
        });

        // 5. Fix Debug Buttons
        const debugButtons = container.querySelectorAll('button[data-action="debugConnections"]');
        debugButtons.forEach(button => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (button.dataset.condHandlerAttached === 'true') return;
            button.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            button.addEventListener('click', (e) => {
                this.debugConnectionInfo();
                this.debugResponseDataAvailability();
            });
        });
    }

    initializeResponseDataSystem() {

        this._responseDataRefreshInterval = setInterval(() => {
            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]?.type === 'condition') {
                this.refreshNodeResponseFields(nodeId);
            }
        }, 2000);

        this._originalTestWorkflow = this.workflowIO.testWorkflow.bind(this.workflowIO);
        this.workflowIO.testWorkflow = async (...args) => {
            const result = await this._originalTestWorkflow(...args);

            if (result) {
                setTimeout(() => {
                    this.refreshAllResponseFields();
                }, 1000);
            }

            return result;
        };
    }


    setupResponseFieldRefresh(nodeId, container) {
        const refreshFields = () => {
            if (this.state.workflowTestResults) {
                this.populateLeftOperandDropdown(nodeId, container);
            }
        };

        let lastTestTimestamp = this.state.lastTestTimestamp;
        const checkTestResults = () => {
            if (this.state.lastTestTimestamp !== lastTestTimestamp) {
                lastTestTimestamp = this.state.lastTestTimestamp;
                refreshFields();
            }
        };

        this._testResultInterval = setInterval(checkTestResults, 1000);
    }


    handleSourceDataChange(nodeId, sourceType) {

        this.updateNodeConfig(nodeId, 'sourceData', sourceType);

        if (sourceType !== 'previous_response') {
            this.updateNodeConfig(nodeId, 'previousNodeId', '');
            this.updateNodeConfig(nodeId, 'dataPath', '');
            this.updateNodeConfig(nodeId, 'leftOperand', '');
        }

        setTimeout(() => {
            this.setupConfigEventHandlers();
        }, 100);
    }


    handleManualDataPathInput(nodeId, dataPath) {

        this.updateNodeConfig(nodeId, 'dataPath', dataPath);

        const nodeConfig = this.state.nodeConfigs[nodeId];
        const previousNodeId = nodeConfig.config.previousNodeId;

        if (previousNodeId && dataPath) {
            const fieldValue = this.workflowIO.getFieldValue(previousNodeId, dataPath);

            if (fieldValue !== null) {
                this.updateNodeConfig(nodeId, 'leftOperand', String(fieldValue));
                this.notification.add(`✅ Field value found: ${fieldValue}`, {
                    type: 'success',
                });
            } else {
                this.updateNodeConfig(nodeId, 'leftOperand', '');
                this.notification.add(`❌ Path "${dataPath}" not found in response`, {
                    type: 'warning',
                });
            }
        }
    }


    getOperatorSymbol(operator) {
        const symbols = {
            'equals': '==',
            'not_equals': '!=',
            'greater_than': '>',
            'less_than': '<',
            'greater_equals': '>=',
            'less_equals': '<=',
            'contains': 'contains',
            'starts_with': 'starts with',
            'ends_with': 'ends with',
            'exists': 'exists'
        };
        return symbols[operator] || operator;
    }


    handlePreviousNodeChange(nodeId, previousNodeId) {
        // ============================================================
        // 1. DEBOUNCE (Prevents Double Notifications)
        // ============================================================
        // We create a timestamp. If this function runs again within 500ms, we stop it.
        const now = Date.now();
        if (this._lastNodeChangeTime && (now - this._lastNodeChangeTime < 500)) {
            console.warn(" Ignored duplicate change event (Debounced)");
            return;
        }
        this._lastNodeChangeTime = now;

        this.updateNodeConfig(nodeId, 'previousNodeId', previousNodeId);
        this.updateNodeConfig(nodeId, 'dataPath', '');
        this.updateNodeConfig(nodeId, 'leftOperand', '');

        if (previousNodeId) {
            // ============================================================
            // 2. ROBUST NODE LOOKUP
            // ============================================================
            let previousNode = this.state.nodeConfigs[previousNodeId];

            if (!previousNode && this.workflowIO && typeof this.workflowIO.getNode === 'function') {
                previousNode = this.workflowIO.getNode(previousNodeId);
            }

            // ============================================================
            // 3. LOGIC & NOTIFICATIONS
            // ============================================================
            const isLoopNode = previousNode && String(previousNode.type).toLowerCase() === 'loop';
            const hasResponseData = this.workflowIO.getNodeResponseData(previousNodeId);

            if (isLoopNode) {
                this.notification.add(
                    `Loop node selected. The 'item' variable is available.`,
                    { type: 'info' }
                );
            } else if (!hasResponseData) {
                this.notification.add(
                    ` Selected node has no response data. Run workflow test first.`,
                    { type: 'warning' }
                );
            } else {
                const responseData = this.workflowIO.getNodeResponseData(previousNodeId);
                const fields = responseData ? this.workflowIO.getResponseFields(responseData) : [];
                this.notification.add(
                    ` ${fields.length} response fields available.`,
                    { type: 'info' }
                );
            }
        }

        // ============================================================
        // 4. SAFE UI UPDATE
        // ============================================================
        setTimeout(() => {
            const configPanel = this.configPanelRef ? this.configPanelRef.el : null;
            if (configPanel && typeof this.populateLeftOperandDropdown === 'function') {
                try {
                    this.populateLeftOperandDropdown(nodeId, configPanel);
                } catch (e) {
                    console.warn("⚠️ UI Update skipped:", e.message);
                }
            }
            this.setupConfigEventHandlers();
        }, 100);
    }


    handleResponseFieldChange(nodeId, dataPath) {

        this.updateNodeConfig(nodeId, 'dataPath', dataPath);

        const nodeConfig = this.state.nodeConfigs[nodeId];
        const previousNodeId = nodeConfig.config.previousNodeId;

        if (previousNodeId && dataPath) {
            const fieldValue = this.workflowIO.getFieldValue(previousNodeId, dataPath);

            if (fieldValue !== null) {
                this.updateNodeConfig(nodeId, 'leftOperand', String(fieldValue));
                this.notification.add(`✅ Left operand auto-filled with value: ${fieldValue}`, {
                    type: 'success',
                    timeout: 3000
                });
            } else {
                this.updateNodeConfig(nodeId, 'leftOperand', '');
                this.notification.add(`❌ Field "${dataPath}" not found in response data`, {
                    type: 'warning',
                    timeout: 3000
                });
            }
        }

        setTimeout(() => {
            this.setupConfigEventHandlers();
        }, 100);
    }


    getNodeError(nodeId) {
        return this.workflowIO?.getNodeError(nodeId);
    }

    getFlowResults() {
        return this.workflowIO?.getFlowResults() || [];
    }

    clearNodeResponseAndError(nodeId) {
        this.clearNodeResponse(nodeId);

        if (this.state.nodeErrors && this.state.nodeErrors[nodeId]) {
            delete this.state.nodeErrors[nodeId];
        }

        this.nodeManager.updateNodeStatus(nodeId);
        this.state.configUpdateCounter++;
    }


    refreshAllNodeStatuses() {
        this.state.workflowNodes.forEach(nodeId => {
            this.nodeManager.updateNodeStatus(nodeId);
        });
        this.connectionManager.updateConnections();
        this.state.configUpdateCounter++;
    }

    async runEnhancedWorkflowTest() {
        try {
            this.state.nodeErrors = {};

            Object.keys(this.state.nodeResponses).forEach(nodeId => {
                const nodeType = this.state.nodeConfigs[nodeId]?.type;
                if (nodeType !== 'get' && nodeType !== 'post' &&
                    nodeType !== 'put' && nodeType !== 'delete') {
                    this.clearNodeResponse(nodeId);
                }
            });

            this.notification.add("Testing workflow with enhanced flow tracking...", { type: 'info' });

            const result = await this.workflowIO.testWorkflow();

            this.refreshAllNodeStatuses();

            this.state.workflowNodes.forEach(nodeId => {
                this.nodeManager.updateNodeStatus(nodeId);
            });

            return result;
        } catch (error) {
            this.notification.add(`Workflow test failed: ${error.message}`, { type: 'danger' });
        }
    }

    setupInputHandlers(container) {
        const inputs = container.querySelectorAll('input[type="text"], input[type="number"], input[type="password"], textarea');
        inputs.forEach(input => {
            const key = input.dataset.configKey;

            // 1. Skip Auth Inputs so XML/OWL can manage them (Username, Password, etc.)
            const authKeys = ['username', 'password', 'token', 'apiKey', 'keyName'];
            if (key && authKeys.includes(key)) return;

            // 2. CRITICAL FIX: Do NOT clone. Check if handler exists on the ORIGINAL node.
            if (input.dataset.handlerAttached === 'true') {
                return;
            }

            // 3. Mark as attached
            input.dataset.handlerAttached = 'true';

            // 4. Attach listener to the ORIGINAL input
            input.addEventListener('input', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId || !key) return;

                let value = e.target.value;
                if (e.target.type === 'number') {
                    value = parseInt(value) || 0;
                }
                this.updateNodeConfig(nodeId, key, value);
            });

            input.addEventListener('blur', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId || !key) return;
                this.updateNodeConfig(nodeId, key, e.target.value);
            });

            // Restore value logic (only if not managed by OWL t-att-value)
            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                if (key && this.state.nodeConfigs[nodeId].config[key] !== undefined) {
                    input.value = this.state.nodeConfigs[nodeId].config[key];
                }
            }
        });
    }

    setupSelectHandlers(container) {
        const selects = container.querySelectorAll('select');
        selects.forEach(select => {
            const key = select.dataset.configKey;

            // 1. Skip Auth Type so XML/OWL can manage the change event
            // This ensures your updateAuthType function in XML actually fires!
            if (key === 'authType' || key === 'keyLocation') return;

            // 2. CRITICAL FIX: Do NOT clone.
            if (select.dataset.handlerAttached === 'true') {
                return;
            }

            // 3. Mark as attached
            select.dataset.handlerAttached = 'true';

            // 4. Attach listener to the ORIGINAL select
            select.addEventListener('change', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId || !key) return;
                this.updateNodeConfig(nodeId, key, e.target.value);
            });

            // Restore value from state
            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                if (key && this.state.nodeConfigs[nodeId].config[key] !== undefined) {
                    select.value = this.state.nodeConfigs[nodeId].config[key];
                }
            }
        });
    }

    setupButtonHandlers(container) {

        const addParamButtons = container.querySelectorAll('button[data-action="addParam"]');
        addParamButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                this.addParamFromInputs(nodeId, 'params');
            });
        });

        const addHeaderButtons = container.querySelectorAll('button[data-action="addHeader"]');
        addHeaderButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                this.addParamFromInputs(nodeId, 'headers');
            });
        });

        const removeButtons = container.querySelectorAll('button[data-action="removeParam"]');
        removeButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                const paramType = e.target.dataset.paramType;
                const index = parseInt(e.target.dataset.index);
                this.removeParam(nodeId, paramType, index);
            });
        });

        const bodyTemplateButtons = container.querySelectorAll('button[data-action="applyBodyTemplate"]');
        bodyTemplateButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                const templateType = e.target.dataset.templateType;
                this.applyBodyTemplate(nodeId, templateType);
            });
        });

        const testButtons = container.querySelectorAll('button[data-action="testApi"]');
        testButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                this.runApiTest(nodeId);
            });
        });

        const clearResponseButtons = container.querySelectorAll('button[data-action="clearResponse"]');
        clearResponseButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;
                this.clearNodeResponse(nodeId);
            });
        });
    }

    onDragOver(ev) {
        ev.preventDefault();
        ev.dataTransfer.dropEffect = 'copy';
    }

    onDragLeave(ev) {
    }

    onDrop(ev) {
        ev.preventDefault();
        const nodeType = ev.dataTransfer.getData('text/plain');
        if (!nodeType) return;

        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();
        const x = ev.clientX - rect.left - 80;
        const y = ev.clientY - rect.top - 40;

        this.nodeManager.createWorkflowNode(nodeType, x, y);
        this.state.showInstructions = false;
    }


    selectNode(nodeId) {

        if (!this.state.rightPanelOpen) {
            this.state.rightPanelOpen = true;
            // Trigger resize to fix connection lines after animation
            setTimeout(() => window.dispatchEvent(new Event('resize')), 310);
        }

        // Switch to Node View (in case it was on Global Settings)
        this.state.rightPanelMode = 'node';

        // --- Your existing logic follows below ---
        this.savePendingChanges();

        document.querySelectorAll('.workflow-node').forEach(node =>
            node.classList.remove('selected')
        );

        const nodeElement = document.getElementById(nodeId);
        if (nodeElement) {
            nodeElement.classList.add('selected');
        }
        this.state.selectedNode = nodeId;

        // ... (rest of your existing code: condition logic, timeouts, loop UI, etc.) ...
        if (this.state.nodeConfigs[nodeId]?.type === 'condition') {
            setTimeout(() => {
                const configPanel = this.configPanelRef.el;
                if (configPanel) {
                    this.populateLeftOperandDropdown(nodeId, configPanel);
                }
            }, 150);
        }
        setTimeout(() => {
            this.setupConfigEventHandlers();
            this.refreshConfigPanelFields();

            if (this.state.nodeConfigs[nodeId] && this.state.nodeConfigs[nodeId].config) {
                this.state.configUpdateCounter++;
            }



        }, 100);
    }

    savePendingChanges() {
        const currentNodeId = this.state.selectedNode;
        100
        if (!currentNodeId) return;

        const textareas = this.configPanelRef.el?.querySelectorAll('textarea[data-config-key]');
        if (textareas) {
            textareas.forEach(textarea => {
                const key = textarea.dataset.configKey;
                const currentValue = this.state.nodeConfigs[currentNodeId]?.config[key];
                const textareaValue = textarea.value;

                if (currentValue !== textareaValue) {
                    this.updateNodeConfig(currentNodeId, key, textareaValue);
                }
            });
        }


    }


    _getPreviousNodesWithResponses(currentNodeId) {
        const nodes = this.state.workflowNodes;
        const connections = this.state.connections;
        const nodeConfigs = this.state.nodeConfigs;
        const nodeTestResults = this.state.nodeTestResults || {};

        const previousNodes = [];


        connections.forEach(conn => {
            if (conn.target === currentNodeId) {
                const sourceNodeId = conn.source;
                const sourceConfig = nodeConfigs[sourceNodeId];

                if (sourceConfig) {
                    const hasResponseData = nodeTestResults[sourceNodeId] &&
                        nodeTestResults[sourceNodeId].response_data;

                    previousNodes.push({
                        id: sourceNodeId,
                        title: this.nodeTemplates.getNodeTitle(sourceConfig.type),
                        type: sourceConfig.type,
                        hasResponseData: !!hasResponseData
                    });
                }
            }
        });
        return previousNodes;
    }


    handleTextareaInput(key, ev) {
        this._pendingTextareaValues = this._pendingTextareaValues || {};
        this._pendingTextareaValues[key] = ev.target.value;
    }

    saveTextareaValue(key, ev) {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const value = this._pendingTextareaValues?.[key] || ev.target.value;

        if (value !== undefined) {
            this.updateNodeConfig(nodeId, key, value);

            if (this._pendingTextareaValues) {
                delete this._pendingTextareaValues[key];
            }
        }
    }


    deselectAllNodes() {
        document.querySelectorAll('.workflow-node').forEach(node =>
            node.classList.remove('selected')
        );
        this.state.selectedNode = null;
    }

    updateNodeConfig(nodeId, key, value) {
        const node = this.state.nodeConfigs[nodeId];
        if (!node) {
            console.warn("updateNodeConfig: node not found:", nodeId);
            return;
        }

        // 1. Create a clean copy of the config
        const updatedConfig = { ...node.config };

        // 2. Apply the change
        updatedConfig[key] = value;

        if (key === 'authType') {
            if (value === 'basic') {
                if (!updatedConfig.basicAuthMethod) {
                    updatedConfig.basicAuthMethod = 'username-password';
                }
            } else if (value === 'api-key') {
                if (!updatedConfig.keyName) updatedConfig.keyName = 'X-API-Key';
                if (!updatedConfig.keyLocation) updatedConfig.keyLocation = 'header';
            }

            const allAuthFields = ['username', 'password', 'token', 'apiKey', 'keyLocation', 'keyName', 'secretKey'];
            let validFields = [];
            if (value === 'basic') validFields = ['username', 'password', 'apiKey', 'secretKey', 'keyLocation', 'keyName', 'basicAuthMethod'];
            if (value === 'bearer') validFields = ['token'];
            if (value === 'api-key') validFields = ['apiKey', 'keyLocation', 'keyName'];

            allAuthFields.forEach(field => {
                if (!validFields.includes(field)) {
                    delete updatedConfig[field];
                }
            });
        }

        // 4. SPECIAL LOGIC: Handle Body Type Changes
        if (key === 'bodyType') {
            if (value === 'form') {
                if (!updatedConfig.formFields || !Array.isArray(updatedConfig.formFields)) {
                    updatedConfig.formFields = [];
                }
                if (updatedConfig.body) {
                    try {
                        const jsonObject = JSON.parse(updatedConfig.body);
                        const formFields = [];
                        Object.entries(jsonObject).forEach(([k, v]) => {
                            formFields.push({
                                key: k,
                                value: typeof v === 'object' ? JSON.stringify(v) : String(v)
                            });
                        });
                        updatedConfig.formFields = formFields;
                    } catch (e) {
                    }
                }
            }
        }

        // 5. Replace config (Triggers OWL Re-render)
        this.state.nodeConfigs[nodeId].config = updatedConfig;

        //  CRUCIAL FIX — update selectedNode so template sees new authType
        if (this.state.selectedNode && this.state.selectedNode.id === nodeId) {
            this.state.selectedNode.config = updatedConfig;
        }

        // 6. Refresh UI & Auto-Save
        this.nodeManager.updateNodeStatus(nodeId);
        this.state.configUpdateCounter++;
        this.queueDraftSave();

        // 7. Re-attach handlers if needed (for dynamic fields)
        if (key === 'authType' || key === 'bodyType') {
            setTimeout(() => this.setupConfigEventHandlers(), 50);
        }
    }


    updateAuthType(nodeId, authType) {

        this.updateNodeConfig(nodeId, 'authType', authType);
    }

    removeParam(nodeId, paramType, index) {
        this.nodeTemplates.removeParam(nodeId, paramType, index);
        this.setupConfigEventHandlers();
    }

    addParamFromInputs(nodeId, paramType) {
        this.nodeTemplates.addParamFromInputs(nodeId, paramType);
        this.setupConfigEventHandlers();
    }

    applyBodyTemplate(nodeId, type) {
        this.nodeTemplates.applyBodyTemplate(nodeId, type);
        this.setupConfigEventHandlers();
    }


    getNodeParams(nodeId) {
        return this.nodeTemplates.getNodeParams(nodeId);
    }

    get selectedNodeConfig() {
        return this.state.selectedNode ? this.state.nodeConfigs[this.state.selectedNode] : null;
    }

    debugNodeConfigs() {
        return this.state.nodeConfigs;
    }


    convertJsonToForm() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (!nodeConfig.config.body) return;

        try {
            const jsonObject = JSON.parse(nodeConfig.config.body);
            const formFields = [];

            Object.entries(jsonObject).forEach(([key, value]) => {
                formFields.push({
                    key: key,
                    value: typeof value === 'object' ? JSON.stringify(value) : String(value)
                });
            });

            this.updateNodeConfig('formFields', formFields);
            this.notification.add("JSON converted to form data!", { type: 'success' });
        } catch (error) {
            this.notification.add("Invalid JSON format", { type: 'danger' });
        }
    }


    refreshConfigPanelFields() {
        const configPanel = this.configPanelRef.el;
        if (!configPanel) {
            console.warn(' Config panel not available');
            return;
        }

        this.updateInputFields(configPanel);
        this.updateSelectFields(configPanel);
        this.updateTextareaFields(configPanel);

        const nodeId = this.state.selectedNode;
        if (nodeId && this.state.nodeConfigs[nodeId]?.type === 'condition') {
            this.populateLeftOperandDropdown(nodeId, configPanel);
        }
    }

    cleanup() {
        if (this._testResultInterval) {
            clearInterval(this._testResultInterval);
            this._testResultInterval = null;
        }

        if (this._responseDataRefreshInterval) {
            clearInterval(this._responseDataRefreshInterval);
            this._responseDataRefreshInterval = null;
        }

        if (this._originalTestWorkflow) {
            this.workflowIO.testWorkflow = this._originalTestWorkflow;
            this._originalTestWorkflow = null;
        }
    }

    getAvailableResponseFields(nodeId) {
        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (!nodeConfig) return [];

        const previousNodeId = nodeConfig.config.previousNodeId;
        if (!previousNodeId) return [];

        const responseData = this.workflowIO.getNodeResponseData(previousNodeId);
        if (!responseData) return [];

        return this.workflowIO.getResponseFields(responseData);
    }

    refreshAllResponseFields() {
        Object.keys(this.state.nodeConfigs).forEach(nodeId => {
            const nodeConfig = this.state.nodeConfigs[nodeId];
            if (nodeConfig.type === 'condition') {
                this.refreshNodeResponseFields(nodeId);
            }
        });
    }

    refreshNodeResponseFields(nodeId) {
        const configPanel = this.configPanelRef.el;
        if (!configPanel || this.state.selectedNode !== nodeId) return;

        this.populateLeftOperandDropdown(nodeId, configPanel);
    }

    /**
     * Update input fields with current node configuration
     */
    updateInputFields(container) {
        const inputs = container.querySelectorAll('input[type="text"], input[type="number"], input[type="password"]');
        inputs.forEach(input => {
            const key = input.dataset.configKey;
            if (!key) return;

            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                const value = this.state.nodeConfigs[nodeId].config[key];
                if (value !== undefined && value !== null) {
                    input.value = value;
                }
            }
        });
    }

    /**
     * Update select fields with current node configuration
     */
    updateSelectFields(container) {
        const selects = container.querySelectorAll('select');
        selects.forEach(select => {
            const key = select.dataset.configKey;
            if (!key) return;

            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                const value = this.state.nodeConfigs[nodeId].config[key];
                if (value !== undefined && value !== null) {
                    select.value = value;
                }
            }
        });
    }

    /**
     * Update textarea fields with current node configuration
     */
    updateTextareaFields(container) {
        const textareas = container.querySelectorAll('textarea');
        textareas.forEach(textarea => {
            const key = textarea.dataset.configKey;
            if (!key) return;

            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                const value = this.state.nodeConfigs[nodeId].config[key];
                if (value !== undefined && value !== null) {
                    textarea.value = value;
                }
            }
        });
    }

    setupTextareaHandlers(container) {
        const textareas = container.querySelectorAll('textarea[data-config-key]');
        textareas.forEach(textarea => {

            // 1. CRITICAL FIX: Do NOT clone.
            if (textarea.dataset.handlerAttached === 'true') {
                return;
            }
            textarea.dataset.handlerAttached = 'true';

            textarea.addEventListener('input', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;

                const key = e.target.dataset.configKey;
                if (!key) return;

                this.updateNodeConfig(nodeId, key, e.target.value);
            });

            textarea.addEventListener('blur', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId) return;

                const key = e.target.dataset.configKey;
                if (!key) return;

                this.updateNodeConfig(nodeId, key, e.target.value);
            });

            const nodeId = this.state.selectedNode;
            if (nodeId && this.state.nodeConfigs[nodeId]) {
                const key = textarea.dataset.configKey;
                if (key && this.state.nodeConfigs[nodeId].config[key] !== undefined) {
                    textarea.value = this.state.nodeConfigs[nodeId].config[key];
                }
            }
        });
    }



    clearNodeResponse(nodeId) {
        if (this.state.nodeResponses[nodeId]) {
            delete this.state.nodeResponses[nodeId];
            this.state.configUpdateCounter++;

        }
    }


    getNodeResponse(nodeId) {
        // 1. Check Full Workflow Results (Preferred - from "Run Full Workflow")
        if (this.state.nodeTestResults && this.state.nodeTestResults[nodeId]) {
            return this.state.nodeTestResults[nodeId];
        }

        if (this.state.nodeResponses && this.state.nodeResponses[nodeId]) {
            return this.state.nodeResponses[nodeId];
        }

        return null;
    }


    storeWorkflowTestResults(testResults) {


        this.state.workflowTestResults = testResults;
        this.state.lastTestTimestamp = new Date().toISOString();

        this.state.configUpdateCounter++;
    }


    async runApiTest(nodeId) {
        // Ensure the node is selected
        this.state.selectedNode = nodeId;
        // Call the smart testing function
        return this.testSelectedNode();
    }

    formatResponseData(responseData) {
        if (!responseData) return "No response data";

        // Internal helper to strip HTML and decode entities
        const cleanString = (str) => {
            if (typeof str !== 'string') return str;
            return str
                .replace(/<[^>]*>?/gm, '')   // 1. Remove HTML tags like <p>, <br>
                .replace(/\\n/g, ' ')        // 2. Remove literal \n characters
                .replace(/\n/g, ' ')         // 3. Remove actual newlines
                .replace(/&nbsp;/g, ' ')     // 4. Fix non-breaking spaces
                .replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(dec)) // 5. Fix entities like &#8217;
                .replace(/\s\s+/g, ' ')      // 6. Collapse multiple spaces into one
                .trim();
        };

        // Internal helper to walk through the JSON object
        const recursiveClean = (obj) => {
            if (Array.isArray(obj)) {
                return obj.map(item => recursiveClean(item));
            } else if (typeof obj === 'object' && obj !== null) {
                const cleaned = {};
                for (let key in obj) {
                    cleaned[key] = recursiveClean(obj[key]);
                }
                return cleaned;
            } else if (typeof obj === 'string') {
                return cleanString(obj);
            }
            return obj;
        };

        try {
            let dataToDisplay = responseData;

            // Extract payload if wrapped in Odoo/Controller metadata
            if (typeof responseData === 'object' && responseData !== null) {
                dataToDisplay = responseData.response_data || responseData.data || responseData.body || responseData;
            }

            // If it's a stringified JSON, parse it first
            if (typeof dataToDisplay === 'string') {
                try {
                    dataToDisplay = JSON.parse(dataToDisplay);
                } catch (e) {
                    return cleanString(dataToDisplay);
                }
            }

            // Apply the deep clean to all values in the object
            const finalCleanedData = recursiveClean(dataToDisplay);

            return JSON.stringify(finalCleanedData, null, 4);

        } catch (error) {
            console.error('Cleaning error:', error);
            return String(responseData);
        }
    }


    toggleOrmMode() {
        this.state.ormAdvancedMode = !this.state.ormAdvancedMode;
    }



    updateOrmDomain(index, property, val) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        const domainRow = config.ormDomains[index];
        domainRow[property] = val;

        if (property === 'field') {
            const search = val.toLowerCase();
            domainRow.filteredFields = (this.state.availableFields || []).filter(f =>
                f.name.toLowerCase().includes(search)
            ).slice(0, 10);
            domainRow.isDropdownOpen = domainRow.filteredFields.length > 0;
        }
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    selectDomainField(index, fieldName) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        config.ormDomains[index].field = fieldName;
        config.ormDomains[index].isDropdownOpen = false;
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    removeOrmDomain(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        config.ormDomains.splice(index, 1);
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }


    syncOrmToValues() {
        const nodeId = this.state.selectedNode;
        if (!nodeId || !this.state.nodeConfigs[nodeId]) return;
        const config = this.state.nodeConfigs[nodeId].config;
        const op = config.operation;

        // 1. Handle Mapper (Create / Write)
        if (['create', 'write'].includes(op)) {
            const obj = {};
            (config.ormFields || []).forEach(f => {
                if (f.key) {
                    let val = f.value;
                    if (typeof val === 'string' && !val.includes('{{')) {
                        if (val.toLowerCase() === 'true') val = true;
                        else if (val.toLowerCase() === 'false') val = false;
                        else if (!isNaN(val) && val.trim() !== "") val = Number(val);
                    }
                    obj[f.key] = val;
                }
            });
            config.field_values_json = JSON.stringify(obj, null, 4);
        }
        // 2. Handle Domain Builder (Search / Count)
        else if (['search', 'search_read', 'search_count'].includes(op)) {
            const domain = (config.ormDomains || []).map(d => {
                let val = d.value;
                if (typeof val === 'string' && !val.includes('{{')) {
                    if (val.toLowerCase() === 'true') val = true;
                    else if (val.toLowerCase() === 'false') val = false;
                    else if (!isNaN(val) && val.trim() !== "") val = Number(val);
                }
                return [d.field, d.operator, val];
            });
            config.field_values_json = JSON.stringify(domain, null, 4);
        }

        this.markDirty(); // Adds the "*" to the Save button
        this.queueDraftSave();
    }


    updateTextareaConfig(nodeId, key, event) {
        const value = event.target.value;

        this.updateNodeConfig(nodeId, key, value);
    }

    getMappingSuggestions(nodeId) {
        const suggestions = [];

        // -------------------------------------------------------------
        // 1. TRAVERSAL LOGIC: Look behind Condition nodes
        // -------------------------------------------------------------
        let dataNode = null;
        let dataNodeId = null;
        let currentScanId = nodeId;

        // Loop up to 10 levels back to prevent infinite loops in case of circular connections
        for (let i = 0; i < 10; i++) {
            // Find connection feeding into the current scan target
            const conn = this.state.connections.find(c => c.target === currentScanId);

            if (!conn) break; // End of the line

            const sourceId = conn.source;
            const sourceNode = this.state.nodeConfigs[sourceId];

            if (!sourceNode) break;

            // If we hit a Condition node, keep stepping back
            if (sourceNode.type === 'condition') {
                currentScanId = sourceId; // Move pointer back one step
                continue;
            }

            // If we found a Data Provider, stop here
            if (['loop', 'get', 'post', 'put', 'delete', 'webhook'].includes(sourceNode.type)) {
                dataNode = sourceNode;
                dataNodeId = sourceId;
                break;
            }

            // If it's Start/Auth/etc, just stop
            break;
        }

        // -------------------------------------------------------------
        // 2. GENERATE SUGGESTIONS (Using the Found Data Node)
        // -------------------------------------------------------------

        if (!dataNode) {
            suggestions.push({
                group: "Status",
                items: [{ value: "", label: "No Data Source Found (Not connected)", disabled: true }]
            });
        } else {


            if (dataNode.type === 'loop') {
                const sample = this.getLoopSampleItem(dataNodeId);

                if (sample) {
                    const fields = this.workflowIO.getResponseFields(sample);
                    suggestions.push({
                        group: `Item Fields (via ${dataNode.type})`, // Helpful label
                        items: fields.map(f => ({
                            value: `{{ item.${f.path} }}`,
                            label: `${f.label} (${f.type})`
                        }))
                    });
                } else {
                    suggestions.push({
                        group: "Help",
                        items: [{ value: "", label: "Loop has no data sample. Run API Test first.", disabled: true }]
                    });
                }
            }

            else {
                const data = this.workflowIO.getNodeResponseData(dataNodeId);

                if (data) {
                    const fields = this.workflowIO.getResponseFields(data);
                    suggestions.push({
                        group: `Response Data (via ${dataNode.type})`,
                        items: fields.map(f => ({
                            value: `{{ data.${f.path} }}`,
                            label: f.label
                        }))
                    });
                } else {
                    suggestions.push({
                        group: "Help",
                        items: [{ value: "", label: "⚠️ Source node has no results. Run 'Test' on it first.", disabled: true }]
                    });
                }
            }
        }

        // -------------------------------------------------------------
        // 3. TRIGGER DATA (Always Available)
        // -------------------------------------------------------------
        suggestions.push({
            group: "Automation Trigger",
            items: [
                { value: '{{ trigger.id }}', label: 'Trigger Record ID' },
                { value: '{{ trigger.name }}', label: 'Trigger Display Name' }
            ]
        });

        return suggestions;
    }
    async addOrmDomain() {
        const nodeId = this.state.selectedNode;
        if (!nodeId || !this.state.nodeConfigs[nodeId]) return;

        const config = this.state.nodeConfigs[nodeId].config;

        // 1. Ensure Odoo fields are loaded in memory for this specific model
        await this.ensureFieldsLoaded(nodeId);

        if (!config.ormDomains) config.ormDomains = [];

        // 2. Add row with pre-filled fields list for the searchable dropdown
        config.ormDomains.push({
            field: '',
            operator: '=',
            value: '',
            isDropdownOpen: false,
            // Pre-fill the dropdown with the first 20 fields for better UX
            filteredFields: (this.state.availableFields || []).slice(0, 20)
        });

        this.state.configUpdateCounter++;
        this.markDirty(); // Ensure the UI knows the workflow has unsaved changes
    }


    async updateOrmDomain(index, property, val) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        const domainRow = config.ormDomains[index];

        domainRow[property] = val;

        if (property === 'field') {
            // Load fields if missing
            if (!this.state.availableFields || this.state.availableFields.length === 0) {
                await this.ensureFieldsLoaded(nodeId);
            }

            // Filter Logic
            const search = val.toLowerCase();
            domainRow.filteredFields = (this.state.availableFields || []).filter(f =>
                f.name.toLowerCase().includes(search) ||
                (f.string && f.string.toLowerCase().includes(search))
            ).slice(0, 20); // Limit results for performance

            domainRow.isDropdownOpen = true;
        }

        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    async onOrmDomainFieldFocus(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        if (!config.ormDomains || !config.ormDomains[index]) return;

        const row = config.ormDomains[index];

        // Ensure fields are loaded
        if (!this.state.availableFields || this.state.availableFields.length === 0) {
            await this.ensureFieldsLoaded(nodeId);
        }

        // Reset filter if input is empty, otherwise filter by current value
        const currentVal = (row.field || '').toLowerCase();
        row.filteredFields = this.state.availableFields.filter(f =>
            f.name.toLowerCase().includes(currentVal) ||
            (f.string && f.string.toLowerCase().includes(currentVal))
        ).slice(0, 20);

        row.isDropdownOpen = true;
        this.state.configUpdateCounter++;
    }


    onOrmDomainFieldBlur(index) {
        setTimeout(() => {
            const nodeId = this.state.selectedNode;
            // Safety check
            if (!nodeId || !this.state.nodeConfigs[nodeId]) return;

            const config = this.state.nodeConfigs[nodeId].config;
            if (config?.ormDomains?.[index]) {
                config.ormDomains[index].isDropdownOpen = false;
                this.state.configUpdateCounter++;
            }
        }, 200);
    }

    selectDomainField(index, fieldName) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        config.ormDomains[index].field = fieldName;
        config.ormDomains[index].isDropdownOpen = false;

        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }


    handleLoopTypeChange(nodeId, loopType) {
        this.updateNodeConfig(nodeId, 'loopType', loopType);

        // Reset relevant fields when loop type changes
        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (nodeConfig) {
            if (loopType === 'fixed') {
                nodeConfig.config.collectionPath = '';
                nodeConfig.config.condition = '';
            } else if (loopType === 'foreach') {
                nodeConfig.config.condition = '';
                nodeConfig.config.maxIterations = 5;
            } else if (loopType === 'conditional') {
                nodeConfig.config.collectionPath = '';
                nodeConfig.config.maxIterations = 1000;
            }
        }

        setTimeout(() => {
            this.setupConfigEventHandlers();
        }, 100);
    }

    setupFixedNodes() {
        const canvas = this.canvasRef && this.canvasRef.el;
        if (!canvas) return;

        const findExisting = (type) => {
            // Check state
            for (const id in this.state.nodeConfigs) {
                if (this.state.nodeConfigs[id] && this.state.nodeConfigs[id].type === type) {
                    if (document.getElementById(id)) return id;
                }
            }
            return null;
        };


        const startX = 150;
        const startY = 250;

        // 2. End Node: 600px to the right of Start (Horizontal Flow)
        const endX = 750;
        const endY = 250;



        let startId = findExisting('start');
        let endId = findExisting('end');
        // let autoId = findExisting('automation');

        // Create Start if missing
        if (!startId) startId = this.nodeManager.createWorkflowNode('start', startX, startY);

        // Create End if missing
        if (!endId) endId = this.nodeManager.createWorkflowNode('end', endX, endY);


        // Lock these IDs so 'Clear Canvas' doesn't delete them
        this.state.fixedNodes = { start: startId, end: endId };
    }

    resetViewPosition() {
        if (this.canvasWrapperRef && this.canvasWrapperRef.el) {
            // Scroll to top-left corner (0,0)
            this.canvasWrapperRef.el.scrollTo({
                top: 0,
                left: 0,
                behavior: 'smooth'
            });
        }
    }


    handleLeftOperandFieldSelect(nodeId, fieldPath) {
        if (!fieldPath) {
            this.updateNodeConfig(nodeId, 'dataPath', '');
            return;
        }

        const nodeConfig = this.state.nodeConfigs[nodeId];
        const previousNodeId = nodeConfig.config.previousNodeId;

        if (previousNodeId && fieldPath) {
            const fieldValue = this.workflowIO.getFieldValue(previousNodeId, fieldPath);
            this.updateNodeConfig(nodeId, 'dataPath', fieldPath);

            if (fieldValue !== null && fieldValue !== undefined) {
                const stringValue = String(fieldValue);
                this.updateNodeConfig(nodeId, 'leftOperand', stringValue);

                this.notification.add(`✅ Left operand set to: "${stringValue}" from field "${fieldPath}"`, {
                    type: 'success',
                    timeout: 3000
                });
            } else {
                this.updateNodeConfig(nodeId, 'leftOperand', '');
                this.notification.add(` Field "${fieldPath}" exists but value is empty`, {
                    type: 'warning',
                    timeout: 3000
                });
            }
        }

        setTimeout(() => {
            this.setupConfigEventHandlers();
        }, 100);
    }

    debugResponseDataAvailability() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) {
            return;
        }

        const nodeConfig = this.state.nodeConfigs[nodeId];
        const previousNodeId = nodeConfig?.config?.previousNodeId;


        if (previousNodeId) {
            const responseData = this.workflowIO.getNodeResponseData(previousNodeId);


            if (responseData) {
                const fields = this.workflowIO.getResponseFields(responseData);
            }
        }

    }

    // =========================================================
    // TESTING MODES
    // =========================================================

    /** Option 1: Safe Test (Dry Run) */
    async testWorkflow() {
        this.notification.add(" Starting Safe Test (Changes will be rolled back)...", { type: 'info' });
        return this._executeWorkflowWithMode({ dry_run: true });
    }

    async runWorkflowReal() {
        this.dialog.add(ConfirmationDialog, {
            body: _t(" WARNING: This will permanently modify your Odoo database. Proceed?"),
            title: _t("Confirm Workflow Execution"),
            confirmLabel: _t("Run Now"),
            cancelLabel: _t("Cancel"),
            confirm: async () => {
                this.notification.add(_t("🚀 Starting Live Execution..."), { type: 'warning' });
                // Pass dry_run: false
                await this._executeWorkflowWithMode({ dry_run: false });
            },
            cancel: () => {

            },
        });
    }

    /** Helper to handle the Odoo ORM Call with dry_run support */
    async _executeWorkflowWithMode(options) {
        try {
            this.state.workflowTestResults = null;
            this.state.nodeTestResults = null;
            this.state.configUpdateCounter++;

            // Get full workflow data
            const payload = this.workflowIO.serializeForSave();
            const workflowData = payload.workflow || payload;

            workflowData.dry_run = options.dry_run;

            // Call Python (api.workflow -> test_workflow)
            const result = await this.orm.call('api.workflow', 'test_workflow', [workflowData]);

            if (result && result.success) {
                this.state.workflowTestResults = result;
                this.state.lastTestTimestamp = new Date().toISOString();

                // Store individual node results for UI status (Green/Red/Grey)
                if (result.results && Array.isArray(result.results)) {
                    this.state.nodeTestResults = {};
                    result.results.forEach(nodeResult => {
                        this.state.nodeTestResults[nodeResult.node_id] = nodeResult;
                    });
                }

                // Refresh UI lines and statuses
                this.connectionManager.updateConnections();
                this.refreshAllNodeStatuses();

                const modeText = options.dry_run ? "Safe Test Complete (Rolled Back)" : "Live Run Complete (Saved)";
                this.notification.add(` ${modeText}`, { type: 'success' });
            } else {
                this.notification.add(` Execution Failed: ${result?.error || result?.message || 'Unknown error'}`, {
                    type: 'danger'
                });
            }
            return result;
        } catch (error) {
            console.error('Execution error:', error);
            this.notification.add(`❌ System Error: ${error.message}`, { type: 'danger' });
        }
    }

    async testSelectedNode() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        this.notification.add("Testing single node...", { type: 'info' });

        const nodeConfig = this.state.nodeConfigs[nodeId];

        // 1. Collect previous node responses from cache for variable substitution
        const previousResponses = {};
        if (this.state.nodeConfigs) {
            for (const prevNodeId of Object.keys(this.state.nodeConfigs)) {
                // Use the helper that checks both full-run and single-run cache
                const cachedResponse = this.workflowIO.getNodeResponse(prevNodeId);
                if (cachedResponse && cachedResponse.response_data) {
                    previousResponses[prevNodeId] = cachedResponse.response_data;
                } else if (cachedResponse && cachedResponse.data) {
                    previousResponses[prevNodeId] = cachedResponse.data;
                }
            }
        }

        try {
            const result = await this.orm.call(
                'api.workflow', // Must be the main model
                'test_single_node',
                [{
                    id: nodeId,
                    type: nodeConfig.type,
                    config: nodeConfig.config,
                    previous_responses: previousResponses  // Pass cached responses
                }]
            );

            this.workflowIO.storeNodeResponse(nodeId, result);
            this.state.workflowTestResults = { success: result.success, results: result.results || [] };
            this.state.lastTestTimestamp = new Date().toISOString(); // Update timestamp
            this.state.configUpdateCounter++;

            if (result.success) {
                this.notification.add(" Single Node Test Success", { type: 'success' });
            } else {
                this.notification.add(`Single Node Test Failed: ${result.message || 'Unknown error'}`, { type: 'danger' });
            }
        } catch (e) {
            console.error(e);
            this.notification.add(` Test Error: ${e.message}`, { type: 'danger' });
        }
    }

    /** Option 3: Test Until Selected Node (Context Aware) */
    async testUntilSelectedNode() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        this.notification.add(` Running until node...`, { type: 'info' });

        // Get full workflow data
        const payload = this.workflowIO.serializeForSave();
        const workflowData = payload.workflow || payload; // Handle structure variations

        // INJECT THE TARGET ID
        workflowData.target_node_id = nodeId;

        // Run the main test engine
        const result = await this.orm.call('api.workflow', 'test_workflow', [workflowData]);

        // Update UI (Reuse existing logic)
        this.workflowIO.storeWorkflowTestResults(result);

        if (result.success) {
            this.notification.add("✅ Partial execution completed.", { type: 'success' });
        } else {
            this.notification.add("❌ Execution failed before target.", { type: 'danger' });
        }

        this.connectionManager.updateConnections();
    }


    async ensureFieldsLoaded(nodeId) {
        const node = this.state.nodeConfigs[nodeId];
        if (!node) return false;

        const modelName = node.config?.model;

        if (!modelName) {
            this.notification.add("Please select an Odoo Model first.", { type: 'warning' });
            return false;
        }

        // Only fetch fields from the server if they aren't already in memory
        if (!this.state.availableFields || this.state.availableFields.length === 0) {
            try {
                const fields = await this.orm.call('api.workflow', 'get_model_fields', [modelName]);
                this.state.availableFields = Array.isArray(fields) ? fields : [];
            } catch (e) {
                console.error("❌ Failed to load fields for model:", modelName, e);
                return false;
            }
        }
        return true;
    }

    /**
     * 1. Add a new row
     */
    async addOrmField() {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        await this.ensureFieldsLoaded(nodeId);

        if (!config.ormFields) config.ormFields = [];

        config.ormFields.push({
            key: '',
            value: '',
            isDropdownOpen: false,
            isValueDropdownOpen: false,
            filteredFields: (this.state.availableFields || []).slice(0, 10),
            valueSuggestions: []
        });

        this.state.configUpdateCounter++;
    }

    /**
     * 2. Handle Typing (Filtering)
     */
    async updateOrmField(index, keyOrValue, val) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        if (!config.ormFields || !config.ormFields[index]) return;

        const row = config.ormFields[index];
        row[keyOrValue] = val;

        if (keyOrValue === 'key') {
            if (!this.state.availableFields) await this.ensureFieldsLoaded(nodeId);

            const search = val.toLowerCase();
            row.filteredFields = this.state.availableFields.filter(f =>
                f.name.toLowerCase().includes(search) ||
                (f.string && f.string.toLowerCase().includes(search))
            ).slice(0, 10);

            row.isDropdownOpen = true;
        }

        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    /**
     * NEW: Handle Value Field Focus
     */
    async onOrmValueFocus(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        // Safety checks
        if (!config.ormFields || !config.ormFields[index]) return;

        const row = config.ormFields[index];

        // 1. Get Variables from Logic Engine
        const suggestions = this.getMappingSuggestions(nodeId);

        // 2. Populate suggestions
        if (suggestions.length > 0) {
            row.valueSuggestions = suggestions;
        } else {
            // Helper message if no data found
            row.valueSuggestions = [{
                group: "Status",
                items: [{ value: "", label: "⚠️ No previous data (Run Test first)", disabled: true }]
            }];
        }

        // 3. Open Dropdown
        row.isValueDropdownOpen = true;
        this.state.configUpdateCounter++;
    }

    /**
     * NEW: Close Key Dropdown on Blur
     */
    onOrmKeyBlur(index) {
        setTimeout(() => {
            const nodeId = this.state.selectedNode;
            const config = this.state.nodeConfigs[nodeId]?.config;
            if (config?.ormFields?.[index]) {
                config.ormFields[index].isDropdownOpen = false;
                this.state.configUpdateCounter++;
            }
        }, 200);
    }

    closeAllOrmDropdowns() {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId]?.config;
        (config?.ormFields || []).forEach(f => {
            f.isDropdownOpen = false;
            f.isValueDropdownOpen = false;
        });
        this.state.configUpdateCounter++;
    }

    /**
     * NEW: Select from Value Dropdown (Response Data)
     */
    onOrmValueBlur(index) {
        // Delay closing to allow the "Click" event on the item to register
        setTimeout(() => {
            const nodeId = this.state.selectedNode;
            if (!nodeId || !this.state.nodeConfigs[nodeId]) return;

            const config = this.state.nodeConfigs[nodeId].config;
            if (config?.ormFields?.[index]) {
                config.ormFields[index].isValueDropdownOpen = false;
                this.state.configUpdateCounter++;
            }
        }, 200);
    }

    selectMapperValue(index, valueExpression) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        // 1. Set the Input Value
        config.ormFields[index].value = valueExpression;

        // 2. Close Dropdown
        config.ormFields[index].isValueDropdownOpen = false;

        // 3. Save Changes to JSON
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    /**
     * 3. Handle Focus (Open Dropdown)
     */
    async onOrmKeyFocus(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        if (!config.ormFields || !config.ormFields[index]) return;

        // Close ALL other open dropdowns first
        (config.ormFields || []).forEach((f, i) => {
            if (i !== index) {
                f.isDropdownOpen = false;
                f.isValueDropdownOpen = false;
            }
        });

        const row = config.ormFields[index];

        await this.ensureFieldsLoaded(nodeId);

        const search = (row.key || '').toLowerCase();
        row.filteredFields = this.state.availableFields.filter(f =>
            f.name.toLowerCase().includes(search)
        ).slice(0, 10);

        row.isDropdownOpen = true;
        this.state.configUpdateCounter++;
    }

    /**
     * 4. Select from Dropdown
     */
    selectMapperField(index, fieldName) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        config.ormFields[index].key = fieldName;
        config.ormFields[index].isDropdownOpen = false;

        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    /**
     * 5. Remove Row
     */
    removeOrmField(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        config.ormFields.splice(index, 1);
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }

    populateLeftOperandDropdown(nodeId, container) {

    }

    // 1. Logic to get the sample data from a loop (Safe to keep)
    getLoopSampleItem(loopNodeId) {
        const loopNode = this.state.nodeConfigs[loopNodeId];
        if (!loopNode) return null;

        // 1. Find the Source Node (Config or Connection)
        let sourceNodeId = loopNode.config.previousNodeId;
        if (!sourceNodeId && this.state.connections) {
            const conn = this.state.connections.find(c => c.target === loopNodeId);
            if (conn) sourceNodeId = conn.source;
        }

        if (!sourceNodeId) {
            console.warn(" Loop node has no input connection.");
            return null;
        }

        // 2. Get Data via WorkflowIO (The correct data store)
        const sourceData = this.workflowIO.getNodeResponseData(sourceNodeId);
        if (!sourceData) {
            console.warn(" No test data found for the previous node. Run 'Test Until Here' first.");
            return null;
        }

        // 3. Extract the List
        let collection = sourceData;
        const path = loopNode.config.collectionPath;

        if (path && path.trim() !== '' && path.trim() !== '$') {
            // Use local helper to extract nested data
            collection = this._js_extract_json_path(sourceData, path);
        } else {
            // Auto-detect list if path is root ($) or empty
            if (!Array.isArray(collection) && collection && typeof collection === 'object') {
                if (Array.isArray(collection.data)) collection = collection.data;
                else if (Array.isArray(collection.result)) collection = collection.result;
                else if (Array.isArray(collection.records)) collection = collection.records;
            }
        }

        // 4. Return First Item as Sample
        if (Array.isArray(collection) && collection.length > 0) {
            return collection[0];
        }

        return null;
    }

    // -------------------------------------------------------------------------
    // 3. HELPER: JS JSON PATH EXTRACTOR (New)
    // -------------------------------------------------------------------------
    _js_extract_json_path(data, path) {
        if (!path) return data;
        const parts = path.split('.');
        let current = data;

        for (const part of parts) {
            if (current === null || current === undefined) return null;
            if (part === '$') continue;

            // Handle array index: "items[0]"
            if (part.includes('[') && part.includes(']')) {
                const key = part.substring(0, part.indexOf('['));
                const index = parseInt(part.substring(part.indexOf('[') + 1, part.indexOf(']')));

                if (key) current = current[key];
                if (Array.isArray(current) && current[index] !== undefined) {
                    current = current[index];
                } else {
                    return null;
                }
            } else {
                current = current[part];
            }
        }
        return current;
    }

    // 2. NEW FUNCTION: Returns the Options Array (Does NOT touch DOM)
    getLeftOperandOptions(nodeId) {
        if (!this.state.nodeConfigs || !this.state.nodeConfigs[nodeId]) return [];

        const nodeConfig = this.state.nodeConfigs[nodeId];
        let previousNodeId = nodeConfig.config.previousNodeId;

        // Auto-detect connection if not explicitly selected
        if (!previousNodeId && this.workflowIO) {
            const inputConn = this.workflowIO.getInputConnectedNode(nodeId);
            if (inputConn) previousNodeId = inputConn;
        }

        if (!previousNodeId) {
            return [{
                group: "Status",
                items: [{ value: "", label: "⚠️ No Connected Node", disabled: true }]
            }];
        }

        const previousNode = this.state.nodeConfigs[previousNodeId];
        if (!previousNode) return [];

        const options = [];

        // === SCENARIO A: Connected to LOOP Node ===
        if (String(previousNode.type).toLowerCase() === 'loop') {


            const sampleItem = this.getLoopSampleItem(previousNodeId);
            if (sampleItem && this.workflowIO) {
                const fields = this.workflowIO.getResponseFields(sampleItem);
                options.push({
                    group: "Item Properties",
                    items: fields.map(f => ({
                        value: "item." + f.path,
                        label: f.label
                    }))
                });
            }
        } else {
            if (this.workflowIO) {
                const responseData = this.workflowIO.getNodeResponseData(previousNodeId);
                if (responseData) {
                    const fields = this.workflowIO.getResponseFields(responseData);
                    options.push({
                        group: "Response Fields",
                        items: fields.map(f => ({
                            value: f.path,
                            label: f.label
                        }))
                    });
                } else {
                    // Warn if no data is available
                    options.push({
                        group: "Status",
                        items: [{ value: "", label: "⚠️ No Data (Run Test First)", disabled: true }]
                    });
                }
            }
        }
        return options;
    }


    addOption(select, value, text, disabled) {
        var opt = document.createElement('option');
        opt.value = value;
        opt.textContent = text;
        if (disabled) opt.disabled = true;
        select.appendChild(opt);
    }


    clearWorkflowCanvas() {
        this.nodeManager.clearCanvas();
    }

    zoomIn() {
        if (this.state.zoomLevel < 2.0) {
            this.state.zoomLevel = parseFloat((this.state.zoomLevel + 0.1).toFixed(1));
        }
    }

    zoomOut() {
        if (this.state.zoomLevel > 0.5) {
            this.state.zoomLevel = parseFloat((this.state.zoomLevel - 0.1).toFixed(1));
        }
    }

    resetZoom() {
        this.state.zoomLevel = 1.0;
    }

    // ---------------------------------------------------------
    // 🖐️ CANVAS PANNING (GRAB & DRAG) LOGIC
    // ---------------------------------------------------------

    onCanvasMouseDown(ev) {
        // Only pan if clicking on the background (not on a node)
        // We check if the target has the class 'canvas' or 'canvas-scroll-wrapper'
        if (ev.target.classList.contains('canvas') || ev.target.classList.contains('canvas-scroll-wrapper')) {
            this.isPanning = true;
            this.panStartX = ev.clientX;
            this.panStartY = ev.clientY;

            // Remember where the scrollbar currently is
            const wrapper = this.canvasWrapperRef.el;
            this.scrollStartX = wrapper.scrollLeft;
            this.scrollStartY = wrapper.scrollTop;

            // Change cursor to grabbing
            wrapper.style.cursor = 'grabbing';
            ev.preventDefault(); // Prevent text selection
        }
    }

    onCanvasMouseMove(ev) {
        if (!this.isPanning) return;

        const wrapper = this.canvasWrapperRef.el;

        // Calculate how far we moved the mouse
        const dx = ev.clientX - this.panStartX;
        const dy = ev.clientY - this.panStartY;

        // Move the scrollbars
        wrapper.scrollLeft = this.scrollStartX - dx;
        wrapper.scrollTop = this.scrollStartY - dy;
    }

    onCanvasMouseUp(ev) {
        if (this.isPanning) {
            this.isPanning = false;
            // Reset cursor to grab
            if (this.canvasWrapperRef.el) {
                this.canvasWrapperRef.el.style.cursor = 'grab';
            }
        }
    }

    // =========================================================
    // ↩️ UNDO / REDO SYSTEM
    // =========================================================

    /**
     * Call this BEFORE making any significant change (Move, Add, Delete, Connect)
     */
    addToHistory() {
        // 1. Create a deep copy of the CURRENT state
        const snapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });

        // 2. Push to Past
        this.history.past.push(snapshot);

        // 3. Limit history size (e.g. 50 steps) to save memory
        if (this.history.past.length > 50) {
            this.history.past.shift(); // Remove oldest
        }

        // 4. Clear Future (New action invalidates redo path)
        this.history.future = [];

    }

    undo() {
        if (this.history.past.length === 0) return;

        // 1. Save CURRENT state to Future (so we can Redo)
        const currentSnapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });
        this.history.future.push(currentSnapshot);

        // 2. Get the last state from Past
        const previousSnapshot = this.history.past.pop();
        this._applySnapshot(previousSnapshot);

        this.notification.add("↩️ Undone", { type: "info", timeout: 1000 });
    }

    redo() {
        if (this.history.future.length === 0) return;

        // 1. Save CURRENT state to Past (so we can Undo again)
        const currentSnapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });
        this.history.past.push(currentSnapshot);

        // 2. Get the next state from Future
        const nextSnapshot = this.history.future.pop();
        this._applySnapshot(nextSnapshot);

        this.notification.add("↪️ Redone", { type: "info", timeout: 1000 });
    }

    _applySnapshot(jsonString) {
        try {
            const data = JSON.parse(jsonString);


            const nodesArray = Object.values(data.nodeConfigs);

            const restorePayload = {
                nodes: nodesArray,
                connections: data.connections
            };


            this.workflowIO.loadWorkflowData(restorePayload);

            // 3. Restore auxiliary state
            if (data.nodeIdMap) this.state.nodeIdMap = data.nodeIdMap;

            // 4. Restore Selection (Optional: Deselect to prevent config errors)
            this.state.selectedNode = null;

        } catch (e) {
            console.error("❌ Undo/Redo Failed:", e);
            this.notification.add("Failed to restore state", { type: 'danger' });
        }
    }

    handleGlobalKeyDown(ev) {
        // 1. Ignore shortcuts if the user is currently typing in an input, textarea, or contentEditable div
        const activeTag = document.activeElement.tagName.toLowerCase();
        if (activeTag === 'input' || activeTag === 'textarea' || document.activeElement.isContentEditable) {
            return;
        }

        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const cmdOrCtrl = isMac ? ev.metaKey : ev.ctrlKey;

        // 2. Undo: Cmd/Ctrl + Z
        if (cmdOrCtrl && ev.key === 'z' && !ev.shiftKey) {
            ev.preventDefault();
            this.undo();
        }

        // 3. Redo: Cmd/Ctrl + Y (Win) OR Cmd/Ctrl + Shift + Z (Mac/Win)
        if ((cmdOrCtrl && ev.key === 'y') || (cmdOrCtrl && ev.shiftKey && ev.key === 'z')) {
            ev.preventDefault();
            this.redo();
        }

        // 4. Delete: Delete or Backspace (only if a connection line is currently selected)
        if (ev.key === 'Delete' || ev.key === 'Backspace') {
            const connId = this.connectionManager.selectedConnectionId;
            if (connId) {
                ev.preventDefault();
                // Save current state to history BEFORE deleting so we can Undo
                this.addToHistory();
                this.connectionManager.removeConnection(connId);
                this.notification.add("Connection removed", { type: 'info', timeout: 2000 });
            }
        }
    }


    handleTouchStart(ev) {
        if (ev.touches.length === 2) {
            ev.preventDefault(); // Prevent default browser zoom
            this.initialPinchDistance = this._getDistance(ev.touches[0], ev.touches[1]);
        }
    }

    handleTouchMove(ev) {
        if (ev.touches.length === 2 && this.initialPinchDistance > 0) {
            ev.preventDefault();
            const currentDistance = this._getDistance(ev.touches[0], ev.touches[1]);
            const scale = currentDistance / this.initialPinchDistance;

            // Apply zoom based on scale
            // If scale > 1, zooming in. If scale < 1, zooming out.
            // We adjust zoomLevel incrementally for smoother control
            if (scale > 1.02) {
                this.zoomIn();
                this.initialPinchDistance = currentDistance; // Reset for continuous zoom
            } else if (scale < 0.98) {
                this.zoomOut();
                this.initialPinchDistance = currentDistance;
            }
        }
    }

    handleTouchEnd(ev) {
        if (ev.touches.length < 2) {
            this.initialPinchDistance = 0;
        }
    }

    _getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    toggleLeftPanel() {
        this.state.leftPanelOpen = !this.state.leftPanelOpen;
        // Trigger resize event so canvas (and lines) recalculate positions
        setTimeout(() => window.dispatchEvent(new Event('resize')), 310);
    }

    toggleRightPanel() {
        this.state.rightPanelOpen = !this.state.rightPanelOpen;
        setTimeout(() => window.dispatchEvent(new Event('resize')), 310);
    }


    updateBodyType(bodyType) {
        this.formManager.updateBodyType(bodyType);
    }

    addFormField() {
        this.formManager.addFormField();
    }

    updateFormField(index, fieldType, value) {
        this.formManager.updateFormField(index, fieldType, value);
    }

    removeFormField(index) {
        this.formManager.removeFormField(index);
    }

    clearAllFormFields() {
        this.formManager.clearAllFormFields();
    }

    exportWorkflow() {
        return this.workflowIO.exportWorkflow();
    }

    saveWorkflow() {
        return this.workflowIO.saveWorkflow();
    }

    importWorkflow(event) {
        return this.workflowIO.importWorkflow(event);
    }

    getConfigurationTemplate(nodeId) {
        return this.nodeTemplates.getConfigurationTemplate(nodeId);
    }
}

WorkflowBuilder.template = "api_workflow_builder.WorkflowBuilder";
registry.category("actions").add("workflow_builder", WorkflowBuilder);
export default WorkflowBuilder;