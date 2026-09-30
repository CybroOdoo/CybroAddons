/** @odoo-module **/

import { Component, useState, onMounted, useRef, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
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
            loadedModel: null,
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
                console.error(" Failed to load models", e);
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

    async selectModel(modelTechnicalName) {
        if (this.state.rightPanelMode === 'settings') {
            this.updateWorkflowSetting('trigger_model', modelTechnicalName);
        } else if (this.state.selectedNode) {
            this.updateNodeConfig(this.state.selectedNode, 'model', modelTechnicalName);
            // Pre-fetch fields for the new model
            await this.ensureFieldsLoaded(this.state.selectedNode);
        }

        // Hide Dropdown
        this.state.isModelListOpen = false;
    }

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
        return this._executeWorkflow({ dry_run: true });
    }

    get draftKey() {
        return this.state.workflowId ? `wb_draft_${this.state.workflowId}` : `wb_draft_new`;
    }

    serializeDraft() {
        return {
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


            this.setupInputHandlers(configPanel);
            this.setupSelectHandlers(configPanel);
            this.setupTextareaHandlers(configPanel);
            this.setupButtonHandlers(configPanel);
            this.setupConditionalNodeHandlers(configPanel);

            const nodeId = this.state.selectedNode;


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

        const previousNodeSelects = container.querySelectorAll('.previous-node-select');
        previousNodeSelects.forEach(select => {
            // --- PREVENT DUPLICATE LISTENERS ---
            if (select.dataset.condHandlerAttached === 'true') return;
            select.dataset.condHandlerAttached = 'true';
            // -----------------------------------

            select.addEventListener('change', (e) => {
                this.handlePreviousNodeChange(nodeId, e.target.value);
                setTimeout(() => {
                    this.setupConfigEventHandlers();
                }, 100);
            });
        });

        const leftOperandSelects = container.querySelectorAll('.response-field-dropdown, select[data-action="leftOperandSelect"]');
        leftOperandSelects.forEach(select => {
            if (select.dataset.condHandlerAttached === 'true') return;
            select.dataset.condHandlerAttached = 'true';

            select.addEventListener('change', (e) => {
                this.handleLeftOperandFieldSelect(nodeId, e.target.value);
            });
        });


        const manualPathInputs = container.querySelectorAll('.manual-json-path');
        manualPathInputs.forEach(input => {
            if (input.dataset.condHandlerAttached === 'true') return;
            input.dataset.condHandlerAttached = 'true';

            input.addEventListener('input', (e) => {
                this.handleManualDataPathInput(nodeId, e.target.value);
            });
            input.addEventListener('blur', (e) => {
                this.handleManualDataPathInput(nodeId, e.target.value);
            });
        });

        const debugButtons = container.querySelectorAll('button[data-action="debugConnections"]');
        debugButtons.forEach(button => {
            if (button.dataset.condHandlerAttached === 'true') return;
            button.dataset.condHandlerAttached = 'true';

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

        const now = Date.now();
        if (this._lastNodeChangeTime && (now - this._lastNodeChangeTime < 500)) {
            console.warn("⚠️ Ignored duplicate change event (Debounced)");
            return;
        }
        this._lastNodeChangeTime = now;

        this.updateNodeConfig(nodeId, 'previousNodeId', previousNodeId);
        this.updateNodeConfig(nodeId, 'dataPath', '');
        this.updateNodeConfig(nodeId, 'leftOperand', '');

        if (previousNodeId) {

            let previousNode = this.state.nodeConfigs[previousNodeId];

            if (!previousNode && this.workflowIO && typeof this.workflowIO.getNode === 'function') {
                previousNode = this.workflowIO.getNode(previousNodeId);
            }


            const isLoopNode = previousNode && String(previousNode.type).toLowerCase() === 'loop';
            const hasResponseData = this.workflowIO.getNodeResponseData(previousNodeId);

            if (isLoopNode) {
                this.notification.add(
                    ` Loop node selected. The 'item' variable is available.`,
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
        return this._executeWorkflow({ dry_run: true, enhanced: true });
    }

    setupInputHandlers(container) {
        const inputs = container.querySelectorAll('input[type="text"], input[type="number"], input[type="password"], textarea');
        inputs.forEach(input => {
            const key = input.dataset.configKey;

            const authKeys = ['username', 'password', 'token', 'apiKey', 'keyName'];
            if (key && authKeys.includes(key)) return;

            if (input.dataset.handlerAttached === 'true') {
                return;
            }

            input.dataset.handlerAttached = 'true';

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


            if (key === 'authType' || key === 'keyLocation') return;

            if (select.dataset.handlerAttached === 'true') {
                return;
            }

            select.dataset.handlerAttached = 'true';

            select.addEventListener('change', (e) => {
                const nodeId = this.state.selectedNode;
                if (!nodeId || !key) return;
                this.updateNodeConfig(nodeId, key, e.target.value);
            });

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
            setTimeout(() => window.dispatchEvent(new Event('resize')), 310);
        }

        this.state.rightPanelMode = 'node';

        this.savePendingChanges();

        document.querySelectorAll('.workflow-node').forEach(node =>
            node.classList.remove('selected')
        );

        const nodeElement = document.getElementById(nodeId);
        if (nodeElement) {
            nodeElement.classList.add('selected');
        }
        this.state.selectedNode = nodeId;

        setTimeout(async () => {
            this.setupConfigEventHandlers();
            this.refreshConfigPanelFields();

            if (this.state.nodeConfigs[nodeId]) {
                if (this.state.nodeConfigs[nodeId].type === 'orm') {
                    await this.ensureFieldsLoaded(nodeId);
                }
                if (this.state.nodeConfigs[nodeId].config) {
                    this.state.configUpdateCounter++;
                }
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

        const updatedConfig = { ...node.config };

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

        this.state.nodeConfigs[nodeId].config = updatedConfig;

        if (this.state.selectedNode && this.state.selectedNode.id === nodeId) {
            this.state.selectedNode.config = updatedConfig;
        }

        this.nodeManager.updateNodeStatus(nodeId);
        this.state.configUpdateCounter++;
        this.queueDraftSave();

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


    convertJsonToForm(nodeId = null) {
        this.formManager.convertJsonToForm(nodeId);
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

    }


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



    storeNodeResponse(nodeId, responseData) {

        this.state.nodeResponses[nodeId] = {
            success: responseData.success,
            status_code: responseData.status_code,
            data: responseData.response_data,
            headers: responseData.response_headers || {},
            response_time: responseData.response_time || 0,
            timestamp: new Date().toISOString(),
            message: responseData.message || 'Test completed'
        };

        this.state.configUpdateCounter++;
    }


    clearNodeResponse(nodeId) {
        if (this.state.nodeResponses[nodeId]) {
            delete this.state.nodeResponses[nodeId];
            this.state.configUpdateCounter++;

        }
    }


    getNodeResponse(nodeId) {
        if (this.state.nodeTestResults && this.state.nodeTestResults[nodeId]) {
            return this.state.nodeTestResults[nodeId];
        }

        if (this.state.nodeResponses && this.state.nodeResponses[nodeId]) {
            return this.state.nodeResponses[nodeId];
        }

        return null;
    }




    async runApiTest(nodeId) {
        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (!nodeConfig) {
            console.error('Node config not found:', nodeId);
            return;
        }

        try {
            this.notification.add("Testing API...", { type: 'info' });

            const result = await this.orm.call(
                'api.workflow.testing',
                'test_single_node',
                [{
                    id: nodeId,
                    type: nodeConfig.type,
                    config: nodeConfig.config
                }]
            );

            this.storeNodeResponse(nodeId, result);

            if (result.success) {
                this.notification.add(
                    ` API Test Successful (${result.status_code}) - ${result.message}`,
                    { type: 'success' }
                );
            } else {
                this.notification.add(
                    ` API Test Failed: ${result.error || result.message}`,
                    { type: 'danger' }
                );
            }
        } catch (error) {
            console.error(' API test error:', error);

            this.storeNodeResponse(nodeId, {
                success: false,
                error: error.message || error,
                status_code: null,
                response_data: null,
                response_headers: {},
                response_time: 0,
                message: `System Error: ${error.message || error}`
            });

            this.notification.add(
                ` API Test Error: ${error.message || error}`,
                { type: 'danger' }
            );
        }
    }

    formatResponseData(responseData) {
        if (!responseData) return "No response data";

        const cleanString = (str) => {
            if (typeof str !== 'string') return str;
            return str
                .replace(/<[^>]*>?/gm, '')
                .replace(/\\n/g, ' ')
                .replace(/\n/g, ' ')
                .replace(/&nbsp;/g, ' ')
                .replace(/&#(\d+);/g, (match, dec) => String.fromCharCode(dec))
                .replace(/\s\s+/g, ' ')
                .trim();
        };

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

            if (typeof responseData === 'object' && responseData !== null) {
                dataToDisplay = responseData.response_data || responseData.data || responseData.body || responseData;
            }

            if (typeof dataToDisplay === 'string') {
                try {
                    dataToDisplay = JSON.parse(dataToDisplay);
                } catch (e) {
                    return cleanString(dataToDisplay);
                }
            }

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

        this.markDirty();
        this.queueDraftSave();
    }


    updateTextareaConfig(nodeId, key, event) {
        const value = event.target.value;

        this.updateNodeConfig(nodeId, key, value);
    }

    getMappingSuggestions(nodeId) {
        const suggestions = [];


        let dataNode = null;
        let dataNodeId = null;
        let currentScanId = nodeId;

        for (let i = 0; i < 10; i++) {
            const conn = this.state.connections.find(c => c.target === currentScanId);

            if (!conn) break; // End of the line

            const sourceId = conn.source;
            const sourceNode = this.state.nodeConfigs[sourceId];

            if (!sourceNode) break;

            if (sourceNode.type === 'condition') {
                currentScanId = sourceId; // Move pointer back one step
                continue;
            }
            if (['loop', 'get', 'post', 'put', 'delete', 'webhook'].includes(sourceNode.type)) {
                dataNode = sourceNode;
                dataNodeId = sourceId;
                break;
            }

            break;
        }

        if (!dataNode) {
            suggestions.push({
                group: "Status",
                items: [{ value: "", label: " No Data Source Found (Not connected)", disabled: true }]
            });
        } else {

            if (dataNode.type === 'loop') {
                suggestions.push({
                    group: "Loop Context",
                    items: [
                        { value: '{{ item }}', label: 'Current Item (Whole Object)' },
                        { value: '{{ index }}', label: 'Iteration Index' }
                    ]
                });

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
                        items: [{ value: "", label: " Loop has no data sample. Run API Test first.", disabled: true }]
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
                        items: [{ value: "", label: " Source node has no results. Run 'Test' on it first.", disabled: true }]
                    });
                }
            }
        }

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

        await this.ensureFieldsLoaded(nodeId);

        if (!config.ormDomains) config.ormDomains = [];

        config.ormDomains.push({
            field: '',
            operator: '=',
            value: '',
            isDropdownOpen: false,
            filteredFields: (this.state.availableFields || []).slice(0, 20)
        });

        this.state.configUpdateCounter++;
        this.markDirty();
    }


    async updateOrmDomain(index, property, val) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        const domainRow = config.ormDomains[index];

        domainRow[property] = val;

        if (property === 'field') {
            if (!this.state.availableFields || this.state.availableFields.length === 0) {
                await this.ensureFieldsLoaded(nodeId);
            }

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

        if (!this.state.availableFields || this.state.availableFields.length === 0) {
            await this.ensureFieldsLoaded(nodeId);
        }

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
            for (const id in this.state.nodeConfigs) {
                if (this.state.nodeConfigs[id] && this.state.nodeConfigs[id].type === type) {
                    if (document.getElementById(id)) return id;
                }
            }
            return null;
        };



        const startX = 150;
        const startY = 250;

        const endX = 750;
        const endY = 250;


        let startId = findExisting('start');
        let endId = findExisting('end');

        if (!startId) startId = this.nodeManager.createWorkflowNode('start', startX, startY);


        if (!endId) endId = this.nodeManager.createWorkflowNode('end', endX, endY);



        this.state.fixedNodes = { start: startId, end: endId };
    }

    resetViewPosition() {
        if (this.canvasWrapperRef && this.canvasWrapperRef.el) {
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


    async testWorkflow() {
        return this._executeWorkflow({ dry_run: true });
    }

    async runWorkflowReal() {
        this.dialog.add(ConfirmationDialog, {
            body: _t(" WARNING: This will permanently modify your Odoo database. Proceed?"),
            title: _t("Confirm Workflow Execution"),
            confirmLabel: _t("Run Now"),
            cancelLabel: _t("Cancel"),
            confirm: async () => {
                await this._executeWorkflow({ dry_run: false });
            },
            cancel: () => { },
        });
    }

    /** Helper to handle the Odoo ORM Call with dry_run support */
    async _executeWorkflow(options) {
        try {
            const modeText = options.dry_run ? "Safe Test" : "Live Execution";
            this.notification.add(`Starting ${modeText}...`, { type: 'info' });

            this.state.workflowTestResults = null;
            this.state.nodeTestResults = null;
            if (options.enhanced) this.state.nodeErrors = {};
            this.state.configUpdateCounter++;

            const payload = this.workflowIO.serializeForSave();
            const workflowData = payload.workflow || payload;
            workflowData.dry_run = options.dry_run;

            const result = await this.orm.call('api.workflow', 'test_workflow', [workflowData]);

            if (result && result.success) {
                this.state.workflowTestResults = result;
                this.state.lastTestTimestamp = new Date().toISOString();

                if (result.results && Array.isArray(result.results)) {
                    this.state.nodeTestResults = {};
                    result.results.forEach(nodeResult => {
                        this.state.nodeTestResults[nodeResult.node_id] = nodeResult;
                    });
                }

                setTimeout(() => {
                    this.refreshAllResponseFields();
                    this.refreshAllNodeStatuses();
                    this.connectionManager.updateConnections();
                    this.setupConfigEventHandlers();
                }, 500);

                this.notification.add(`${modeText} Successful`, { type: 'success' });
            } else {
                this.notification.add(`${modeText} Failed: ${result?.error || result?.message || 'Unknown error'}`, {
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

        this.notification.add(" Testing single node...", { type: 'info' });

        const nodeConfig = this.state.nodeConfigs[nodeId];

        const previousResponses = {};
        for (const [prevNodeId, prevConfig] of Object.entries(this.state.nodeConfigs)) {
            const cachedResponse = this.getNodeResponse(prevNodeId);
            if (cachedResponse && cachedResponse.data) {
                previousResponses[prevNodeId] = cachedResponse.data;
            }
        }

        try {
            const result = await this.orm.call(
                'api.workflow.testing',
                'test_single_node',
                [{
                    id: nodeId,
                    type: nodeConfig.type,
                    config: nodeConfig.config,
                    previous_responses: previousResponses
                }]
            );

            this.storeNodeResponse(nodeId, result);
            this.state.workflowTestResults = { success: result.success };

            if (result.success) {
                this.notification.add("Single Node Test Success", { type: 'success' });
            } else {
                this.notification.add(` Single Node Test Failed: ${result.message || 'Unknown error'}`, { type: 'danger' });
            }
        } catch (e) {
            console.error(e);
            this.notification.add(` Test Error: ${e.message}`, { type: 'danger' });
        }
    }

    async testUntilSelectedNode() {
        const nodeId = this.state.selectedNode;
        if (!nodeId) return;

        this.notification.add(` Running until node...`, { type: 'info' });

        const payload = this.workflowIO.serializeForSave();
        const workflowData = payload.workflow || payload; // Handle structure variations

        workflowData.target_node_id = nodeId;
        workflowData.dry_run = true;

        const result = await this.orm.call('api.workflow', 'test_workflow', [workflowData]);

        this.workflowIO.storeTestResults(result);

        if (result.success) {
            this.notification.add(" Partial execution completed.", { type: 'success' });
        } else {
            this.notification.add(" Execution failed before target.", { type: 'danger' });
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

        // Only fetch fields from the server if they aren't already in memory for THIS model
        if (!this.state.availableFields || this.state.availableFields.length === 0 || this.state.loadedModel !== modelName) {
            try {
                const fields = await this.orm.call('api.workflow', 'get_model_fields', [modelName]);
                this.state.availableFields = Array.isArray(fields) ? fields : [];
                this.state.loadedModel = modelName;
            } catch (e) {
                console.error("❌ Failed to load fields for model:", modelName, e);
                return false;
            }
        }
        return true;
    }


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


    async onOrmValueFocus(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        if (!config.ormFields || !config.ormFields[index]) return;

        const row = config.ormFields[index];

        const suggestions = this.getMappingSuggestions(nodeId);

        if (suggestions.length > 0) {
            row.valueSuggestions = suggestions;
        } else {
            row.valueSuggestions = [{
                group: "Status",
                items: [{ value: "", label: " No previous data (Run Test first)", disabled: true }]
            }];
        }

        row.isValueDropdownOpen = true;
        this.state.configUpdateCounter++;
    }


    onOrmKeyBlur(index) {
        setTimeout(() => {
            const nodeId = this.state.selectedNode;
            const config = this.state.nodeConfigs[nodeId]?.config;
            if (config?.ormFields?.[index]) {
                config.ormFields[index].isDropdownOpen = false;
                this.state.configUpdateCounter++;
            }
        }, 150);
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


    onOrmValueBlur(index) {
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

        config.ormFields[index].value = valueExpression;

        config.ormFields[index].isValueDropdownOpen = false;
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }


    async onOrmKeyFocus(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        if (!config.ormFields || !config.ormFields[index]) return;

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

    selectMapperField(index, fieldName) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;

        config.ormFields[index].key = fieldName;
        config.ormFields[index].isDropdownOpen = false;

        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }


    removeOrmField(index) {
        const nodeId = this.state.selectedNode;
        const config = this.state.nodeConfigs[nodeId].config;
        config.ormFields.splice(index, 1);
        this.syncOrmToValues();
        this.state.configUpdateCounter++;
    }


    getLoopSampleItem(loopNodeId) {
        const loopNode = this.state.nodeConfigs[loopNodeId];
        if (!loopNode) return null;

        let sourceNodeId = loopNode.config.previousNodeId;
        if (!sourceNodeId && this.state.connections) {
            const conn = this.state.connections.find(c => c.target === loopNodeId);
            if (conn) sourceNodeId = conn.source;
        }

        if (!sourceNodeId) {
            console.warn(" Loop node has no input connection.");
            return null;
        }

        const sourceData = this.workflowIO.getNodeResponseData(sourceNodeId);
        if (!sourceData) {
            console.warn(" No test data found for the previous node. Run 'Test Until Here' first.");
            return null;
        }

        let collection = sourceData;
        const path = loopNode.config.collectionPath;

        if (path && path.trim() !== '' && path.trim() !== '$') {
            collection = this._js_extract_json_path(sourceData, path);
        } else {
            if (!Array.isArray(collection) && collection && typeof collection === 'object') {
                if (Array.isArray(collection.data)) collection = collection.data;
                else if (Array.isArray(collection.result)) collection = collection.result;
                else if (Array.isArray(collection.records)) collection = collection.records;
            }
        }

        if (Array.isArray(collection) && collection.length > 0) {
            return collection[0];
        }

        return null;
    }

    _js_extract_json_path(data, path) {
        if (!path) return data;
        const parts = path.split('.');
        let current = data;

        for (const part of parts) {
            if (current === null || current === undefined) return null;
            if (part === '$') continue;

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

    getLeftOperandOptions(nodeId) {
        if (!this.state.nodeConfigs || !this.state.nodeConfigs[nodeId]) return [];

        const nodeConfig = this.state.nodeConfigs[nodeId];
        let previousNodeId = nodeConfig.config.previousNodeId;

        if (!previousNodeId && this.workflowIO) {
            const inputConn = this.workflowIO.getInputConnectedNode(nodeId);
            if (inputConn) previousNodeId = inputConn;
        }

        if (!previousNodeId) {
            return [{
                group: "Status",
                items: [{ value: "", label: " No Connected Node", disabled: true }]
            }];
        }

        const previousNode = this.state.nodeConfigs[previousNodeId];
        if (!previousNode) return [];

        const options = [];

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
                        items: [{ value: "", label: " No Data (Run Test First)", disabled: true }]
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



    onCanvasMouseDown(ev) {
        if (ev.target.classList.contains('canvas') || ev.target.classList.contains('canvas-scroll-wrapper')) {
            this.isPanning = true;
            this.panStartX = ev.clientX;
            this.panStartY = ev.clientY;

            const wrapper = this.canvasWrapperRef.el;
            this.scrollStartX = wrapper.scrollLeft;
            this.scrollStartY = wrapper.scrollTop;

            wrapper.style.cursor = 'grabbing';
            ev.preventDefault();
        }
    }

    onCanvasMouseMove(ev) {
        if (!this.isPanning) return;

        const wrapper = this.canvasWrapperRef.el;

        const dx = ev.clientX - this.panStartX;
        const dy = ev.clientY - this.panStartY;

        wrapper.scrollLeft = this.scrollStartX - dx;
        wrapper.scrollTop = this.scrollStartY - dy;
    }

    onCanvasMouseUp(ev) {
        if (this.isPanning) {
            this.isPanning = false;
            if (this.canvasWrapperRef.el) {
                this.canvasWrapperRef.el.style.cursor = 'grab';
            }
        }
    }

    addToHistory() {
        const snapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });

        this.history.past.push(snapshot);

        if (this.history.past.length > 50) {
            this.history.past.shift(); // Remove oldest
        }
        this.history.future = [];

    }

    undo() {
        if (this.history.past.length === 0) return;

        const currentSnapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });
        this.history.future.push(currentSnapshot);

        const previousSnapshot = this.history.past.pop();
        this._applySnapshot(previousSnapshot);

        this.notification.add(" Undone", { type: "info", timeout: 1000 });
    }

    redo() {
        if (this.history.future.length === 0) return;

        const currentSnapshot = JSON.stringify({
            nodeConfigs: this.state.nodeConfigs,
            workflowNodes: this.state.workflowNodes,
            connections: this.state.connections,
            nodeIdMap: this.state.nodeIdMap,
            fixedNodes: this.state.fixedNodes,
            nodeIdCounter: this.state.nodeIdCounter
        });
        this.history.past.push(currentSnapshot);

        const nextSnapshot = this.history.future.pop();
        this._applySnapshot(nextSnapshot);

        this.notification.add("Redone", { type: "info", timeout: 1000 });
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

            if (data.nodeIdMap) this.state.nodeIdMap = data.nodeIdMap;
            this.state.selectedNode = null;

        } catch (e) {
            console.error(" Undo/Redo Failed:", e);
            this.notification.add("Failed to restore state", { type: 'danger' });
        }
    }

    handleGlobalKeyDown(ev) {
        const activeTag = document.activeElement.tagName.toLowerCase();
        if (activeTag === 'input' || activeTag === 'textarea' || document.activeElement.isContentEditable) {
            return;
        }

        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        const cmdOrCtrl = isMac ? ev.metaKey : ev.ctrlKey;

        if (cmdOrCtrl && ev.key === 'z' && !ev.shiftKey) {
            ev.preventDefault();
            this.undo();
        }

        if ((cmdOrCtrl && ev.key === 'y') || (cmdOrCtrl && ev.shiftKey && ev.key === 'z')) {
            ev.preventDefault();
            this.redo();
        }

        if (ev.key === 'Delete' || ev.key === 'Backspace') {
            const connId = this.connectionManager.selectedConnectionId;
            if (connId) {
                ev.preventDefault();
                this.addToHistory();
                this.connectionManager.removeConnection(connId);
                this.notification.add("Connection removed", { type: 'info', timeout: 2000 });
            }
        }
    }


    handleTouchStart(ev) {
        if (ev.touches.length === 2) {
            ev.preventDefault();
            this.initialPinchDistance = this._getDistance(ev.touches[0], ev.touches[1]);
        }
    }

    handleTouchMove(ev) {
        if (ev.touches.length === 2 && this.initialPinchDistance > 0) {
            ev.preventDefault();
            const currentDistance = this._getDistance(ev.touches[0], ev.touches[1]);
            const scale = currentDistance / this.initialPinchDistance;

            if (scale > 1.02) {
                this.zoomIn();
                this.initialPinchDistance = currentDistance;
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

    convertFormToJson() {
        this.formManager.convertFormToJson();
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