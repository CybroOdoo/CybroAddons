/** @odoo-module **/

import { Component, useState, xml } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";



class WorkflowSaveDialog extends Component {
    setup() {
        this.state = useState({ name: this.props.defaultName || "" });
    }
    onSave() {
        if (this.state.name.trim()) {
            this.props.onConfirm(this.state.name);
            this.props.close();
        }
    }
}
WorkflowSaveDialog.template = xml`
    <Dialog title="'Save Workflow'">
        <div class="p-3">
            <label class="form-label fw-bold">Workflow Name</label>
            <input type="text"
                   class="form-control"
                   t-model="state.name"
                   t-on-keydown="(e) => e.key === 'Enter' ? this.onSave() : null"
                   autofocus="autofocus"/>
            <div class="form-text text-muted">Give your workflow a unique name.</div>
        </div>
        <t t-set-slot="footer">
            <button class="btn btn-secondary" t-on-click="props.close">Cancel</button>
            <button class="btn btn-primary" t-on-click="onSave">Save</button>
        </t>
    </Dialog>
`;
WorkflowSaveDialog.components = { Dialog };

// ... export class WorkflowIO starts here ...
export class WorkflowIO {
    constructor(workflowBuilder) {
        this.workflow = workflowBuilder;
        this.state = workflowBuilder.state;
        this.orm = workflowBuilder.orm;
        this.notification = workflowBuilder.notification;
    }

    async testWorkflow() {
        if (!this.validateWorkflow()) {
            this.notification.add("Workflow validation failed!", { type: 'danger' });
            return;
        }

        try {
            this.notification.add("Testing workflow...", { type: 'info' });
            this.state.nodeErrors = {};

            const workflowData = {
                workflowId: this.state.workflowId,
                nodes: Object.values(this.state.nodeConfigs),
                connections: this.state.connections,
                enhanced_tracking: true,
                track_individual_flows: true,
            };

            const result = await this.orm.call('api.workflow', 'test_workflow', [workflowData]);

            // Store everything (including executed_nodes); the store method will also
            // record executedConnections and repaint exactly once.
            this.storeTestResults(result);

            if (result.success) {
                let successMessage = `✅ Workflow Test Completed: ${result.message}`;
                if (result.flow_results && result.flow_results.length > 0) {
                    const successfulFlows = result.flow_results.filter(flow => flow.success).length;
                    const totalFlows = result.flow_results.length;
                    successMessage += ` | ${successfulFlows}/${totalFlows} flows successful`;
                }
                this.notification.add(successMessage, { type: 'success' });

                if (result.flow_results && result.flow_results.length > 0) {
                    result.flow_results.forEach((flow, index) => {
                        const flowStatus = flow.success ? '✅' : '❌';
                        const flowMessage = flow.success
                            ? `Executed ${flow.executed_nodes ? flow.executed_nodes.length : 0} nodes`
                            : `Failed at: ${flow.failed_node || 'unknown node'}`;

                        this.notification.add(
                            `Flow ${index + 1}: ${flowStatus} ${flowMessage}`,
                            { type: flow.success ? 'success' : 'warning' }
                        );
                    });
                }
            } else {
                this.displayDetailedErrors(result);
            }

            return result;
        } catch (error) {
            this.notification.add("Workflow test failed", { type: 'danger' });
            console.error('Test error:', error);
        }
    }


    storeTestResults(result) {
        this.state.workflowTestResults = result;
        this.state.lastTestTimestamp = new Date().toISOString();
        this.state.nodeErrors = {};
        this.state.nodeTestResults = {};
        this.state.conditionResults = this.state.conditionResults || {};
        this.state.executedConnections = result.executed_connections || [];

        // Standardized node result collection
        const results = result.node_results || result.results || [];
        if (Array.isArray(results)) {
            results.forEach(nodeResult => {
                const nodeId = nodeResult.node_id || nodeResult.id;
                this.state.nodeTestResults[nodeId] = nodeResult;

                // Handle condition results specially
                if (nodeResult.node_type === 'condition' || nodeResult.condition_result !== undefined) {
                    this.state.conditionResults[nodeId] = {
                        result: nodeResult.condition_result,
                        details: nodeResult.evaluation_details || nodeResult.details
                    };
                }

                // Collect errors for UI feedback
                if (!nodeResult.success) {
                    this.state.nodeErrors[nodeId] = {
                        error: nodeResult.error,
                        message: nodeResult.message,
                        status_code: nodeResult.status_code
                    };
                }
            });
        }

        // Standardized flow/path results
        if (result.flow_results) {
            this.state.flowResults = result.flow_results.map(flow => ({
                path: flow.path,
                success: flow.success,
                executed_nodes: flow.executed_nodes || [],
                failed_node: flow.failed_node,
                error: flow.error,
            }));
        } else {
            this.state.flowResults = [];
        }

        this.state.configUpdateCounter++;

        if (this.workflow?.connectionManager) {
            this.workflow.connectionManager.updateConnections();
            // Double-refresh for complex edge routing safety
            requestAnimationFrame(() => this.workflow.connectionManager.updateConnections());
        }
    }



    displayDetailedErrors(result) {
        if (result.flow_results) {
            result.flow_results.forEach((flow, index) => {
                if (!flow.success && flow.failed_node) {
                    const nodeConfig = this.state.nodeConfigs[flow.failed_node];
                    const nodeType = nodeConfig ? nodeConfig.type : 'Unknown';

                    this.notification.add(
                        `❌ Flow ${index + 1} failed at ${nodeType} node: ${flow.error}`,
                        { type: 'danger' }
                    );
                }
            });
        } else if (result.error) {
            this.notification.add(
                `❌ Workflow Test Failed: ${result.error}`,
                { type: 'danger' }
            );
        }
    }

    getNodeError(nodeId) {
        return this.state.nodeErrors ? this.state.nodeErrors[nodeId] : null;
    }

    getFlowResults() {
        return this.state.flowResults || [];
    }



    getNodeResponseData(nodeId) {
        // 1. Get Config & Result (Result might be undefined)
        const nodeConfig = this.state.nodeConfigs[nodeId];
        const nodeResult = this.state.nodeTestResults ? this.state.nodeTestResults[nodeId] : null;

        // 2. Standard Case: If we have a direct result, return it
        if (nodeResult && (nodeResult.response_data || nodeResult.data)) {
            return nodeResult.response_data || nodeResult.data;
        }

        // 3. FIX: Loop Node Logic (Run this even if nodeResult is missing!)
        if (nodeConfig && nodeConfig.type === 'loop') {

            // Case A: Loop iterates over a previous node's list (Foreach)
            if (nodeConfig.config.loopType === 'foreach' && nodeConfig.config.previousNodeId) {

                // Recursively get data from the source of the list
                const sourceData = this.getNodeResponseData(nodeConfig.config.previousNodeId);
                const path = nodeConfig.config.collectionPath || '';

                // Extract the list
                const collection = this.extractValueFromResponse(sourceData, path);

                // Return the FIRST item as a sample for the Condition Node
                if (Array.isArray(collection) && collection.length > 0) {
                    return collection[0];
                }
            }
        }

        return null;
    }

    getConditionResult(nodeId) {
        return this.state.conditionResults ? this.state.conditionResults[nodeId] : null;
    }

    hasPreviousResponses(nodeId) {
        const previousNodes = this.getPreviousNodesWithResponses(nodeId);
        return previousNodes.some(node => node.hasData);
    }


    getPreviousNodesWithResponses(nodeId) {
        if (!this.state.nodeTestResults || !this.state.nodeConfigs || !this.state.connections) {
            return [];
        }

        const previousNodes = [];
        const inputConnections = this.state.connections.filter(conn => conn.target === nodeId);

        // --- PART 1: Connected Nodes ---
        inputConnections.forEach(conn => {
            const sourceNodeId = conn.source;
            const sourceNodeConfig = this.state.nodeConfigs[sourceNodeId];
            const sourceNodeResult = this.state.nodeTestResults[sourceNodeId]; // Might be undefined for Loops

            // Check if connection is active
            if (this._shouldConnectionBeActive(conn, sourceNodeResult)) {

                if (sourceNodeConfig && (sourceNodeResult || sourceNodeConfig.type === 'loop')) {

                    const isLoop = sourceNodeConfig.type === 'loop';

                    // Determine if it has data
                    const resultData = sourceNodeResult ? (sourceNodeResult.response_data || sourceNodeResult.data) : null;
                    const hasData = !!resultData || isLoop;

                    // Determine success (Loops are considered successful for UI purposes if config exists)
                    const isSuccessful = sourceNodeResult ? sourceNodeResult.status === 'success' : isLoop;

                    if (hasData) {
                        previousNodes.push({
                            id: sourceNodeId,
                            title: sourceNodeConfig.title || `Node ${sourceNodeId}`,
                            type: sourceNodeConfig.type,
                            hasData: true,
                            isSuccessful: isSuccessful,
                            connectionType: conn.outputType || 'data',
                            isConnected: true,
                            isConditionBranch: conn.outputType && ['true', 'false'].includes(conn.outputType)
                        });
                    }
                }
            }
        });

        // --- PART 2: Manual Node Selection ---
        const nodeConfig = this.state.nodeConfigs[nodeId];
        if (nodeConfig && nodeConfig.config && nodeConfig.config.previousNodeId) {
            const manualNodeId = nodeConfig.config.previousNodeId;
            const manualNodeConfig = this.state.nodeConfigs[manualNodeId];
            const manualNodeResult = this.state.nodeTestResults[manualNodeId];

            if (manualNodeConfig && !previousNodes.some(n => n.id === manualNodeId)) {

                //  FIX: Same Logic for Manual Nodes
                const isLoop = manualNodeConfig.type === 'loop';
                const resultData = manualNodeResult ? (manualNodeResult.response_data || manualNodeResult.data) : null;
                const hasData = !!resultData || isLoop;
                const isSuccessful = manualNodeResult ? manualNodeResult.status === 'success' : isLoop;

                if (hasData) {
                    previousNodes.push({
                        id: manualNodeId,
                        title: manualNodeConfig.title || `Node ${manualNodeId}`,
                        type: manualNodeConfig.type,
                        hasData: true,
                        isSuccessful: isSuccessful,
                        isManualConfig: true
                    });
                }
            }
        }

        return previousNodes;
    }


    _shouldConnectionBeActive(connection, sourceNodeResult) {
        // If there's no result yet or the source isn't a condition node → always active
        if (!sourceNodeResult || sourceNodeResult.node_type !== 'condition') {
            return true;
        }

        // Retrieve evaluated condition result (true / false / null)
        const conditionData =
            this.state.conditionResults?.[sourceNodeResult.node_id] ||
            this.state.conditionResults?.[sourceNodeResult.id] ||
            {};
        const conditionResult = conditionData.result;

        // 🧭 Determine connection type (true or false)
        const outputType = connection.outputType || 'true';


        // Explicitly match connection type to condition result
        if (conditionResult === true && outputType === 'true') {
            return true;
        }
        if (conditionResult === false && outputType === 'false') {
            return true;
        }

        // If result is null or no match → block this connection
        return false;
    }
    // ✅ NEW HELPER: Get only fields that are Lists/Arrays for the Loop Node
    getArrayFields(responseData) {
        if (!responseData) return [];
        const arrays = [];

        // Helper to format labels (e.g. "order_line" -> "Order Line")
        const formatLabel = (key) => {
            return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        };

        // 1. Check Root (Is the response itself a list?)
        if (Array.isArray(responseData)) {
            arrays.push({
                path: '$',
                label: 'Main Result List (All Records)',
                count: responseData.length
            });

            // 2. Check inside the first item (Does the record have lists? e.g., Order Lines)
            if (responseData.length > 0 && typeof responseData[0] === 'object') {
                const firstItem = responseData[0];
                Object.keys(firstItem).forEach(key => {
                    if (Array.isArray(firstItem[key])) {
                        arrays.push({
                            path: `[0].${key}`, // Technical path for logic engine
                            label: `${formatLabel(key)} (Nested List)`, // Friendly text
                            count: firstItem[key].length
                        });
                    }
                });
            }
        }
        // 3. Check Object (Is the response a Dictionary containing lists?)
        else if (typeof responseData === 'object') {
            Object.keys(responseData).forEach(key => {
                if (Array.isArray(responseData[key])) {
                    arrays.push({
                        path: key,
                        label: formatLabel(key),
                        count: responseData[key].length
                    });
                }
            });
        }

        return arrays;
    }





    clearWorkflowTestResults() {
        this.state.workflowTestResults = null;
        this.state.nodeTestResults = null;
        this.state.lastTestTimestamp = null;
    }

    validateWorkflow() {
        const hasStart = Object.values(this.state.nodeConfigs).some(node => node.type === 'start');
        const hasEnd = Object.values(this.state.nodeConfigs).some(node => node.type === 'end');

        if (!hasStart) {
            this.notification.add("Workflow must have a Start node", { type: 'warning' });
            return false;
        }

        if (!hasEnd) {
            this.notification.add("Workflow should have an End node", { type: 'warning' });
            return false;
        }

        return true;
    }

    exportWorkflow() {
        const workflowData = {
            nodes: Object.values(this.state.nodeConfigs),
            connections: this.state.connections,
            metadata: {
                version: "1.0",
                exportedAt: new Date().toISOString(),
                totalNodes: this.state.workflowNodes.length
            }
        };

        const dataStr = JSON.stringify(workflowData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });

        const link = document.createElement('a');
        link.href = URL.createObjectURL(dataBlob);
        link.download = `workflow-${Date.now()}.json`;
        link.click();

        this.notification.add("Workflow exported successfully!", { type: 'success' });
    }

    importWorkflow(event) {
        const file = event.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                const workflowData = JSON.parse(e.target.result);
                this.loadWorkflowData(workflowData);

                this.notification.add("Workflow imported successfully!", { type: 'success' });
            } catch (error) {
                console.error('❌ Import error:', error);
                this.notification.add("Invalid workflow file", { type: 'danger' });
            }
        };
        reader.readAsText(file);
        event.target.value = '';
    }



    loadWorkflowData(workflowData) {
        if (!this.workflow?.canvasRef?.el) {
            console.warn('⚠ Canvas not ready, skipping load');
            return;
        }
        const canvas = this.workflow.canvasRef.el;



        // 1. Clear Canvas (DOM)
        // Remove all nodes that aren't Start/End (fixed nodes handled below)
        const fixedNodes = this.workflow.state.fixedNodes || {};
        const fixedIds = new Set(Object.values(fixedNodes));

        Array.from(canvas.querySelectorAll('.workflow-node')).forEach(el => {
            // Optional: You can clear everything to be safe
            // if (!fixedIds.has(el.id)) el.remove();
            el.remove(); // Clean slate approach is safer for reload
        });

        // 2. Reset State
        this.workflow.state.connections = [];
        this.workflow.state.nodeIdMap = {};
        this.workflow.state.selectedNode = null;
        this.workflow.state.workflowNodes = [];
        this.workflow.state.nodeConfigs = {};

        // 3. Process Nodes
        const rawNodes = Array.isArray(workflowData?.nodes) ? workflowData.nodes : [];

        // 🟢 RESTORE GLOBAL SETTINGS (The Fix)
        // Find the ghost node we saved earlier
        const automationNode = rawNodes.find(n => n.type === 'automation');

        if (automationNode && automationNode.config) {


            // ✅ FORCE UPDATE THE SIDEBAR STATE
            Object.assign(this.workflow.state.workflowSettings, automationNode.config);

        } else {
            console.warn("⚠️ No automation settings found. Using Defaults.");
            // Reset to default manual mode if no settings found
            this.workflow.state.workflowSettings = {
                trigger_type: 'manual',
                interval_number: 1,
                interval_type: 'hours',
                trigger_model: '',
                trigger_on: 'on_create',
                cron_active: false
            };
        }

        const nodesToRender = rawNodes.filter(n => n.type !== 'automation');

        // 4. Create Visual Nodes
        for (const nodeData of nodesToRender) {
            const originalId = nodeData.id;
            const type = nodeData.type;
            const x = (typeof nodeData.x === 'number') ? nodeData.x : 100;
            const y = (typeof nodeData.y === 'number') ? nodeData.y : 100;

            if (!type) continue;

            // Handle Fixed Nodes (Start/End) - Reuse or Create
            if (['start', 'end'].includes(type)) {
                // If we cleared the canvas in step 1, we just create new ones.
                // It's cleaner than trying to find/match existing DOM elements.
            }

            // Create Visual Node
            const newId = this.workflow.nodeManager.createWorkflowNode(type, x, y, originalId);

            // Restore Config
            if (this.workflow.state.nodeConfigs[newId]) {
                const loadedConfig = nodeData.config ? JSON.parse(JSON.stringify(nodeData.config)) : {};
                this.workflow.state.nodeConfigs[newId].config = loadedConfig;
                // Ensure positions are synced
                this.workflow.state.nodeConfigs[newId].x = x;
                this.workflow.state.nodeConfigs[newId].y = y;
            }

            // Map old ID to new ID (critical for connections)
            if (originalId) this.workflow.state.nodeIdMap[originalId] = newId;
        }

        // 5. Restore Connections
        const rawConns = Array.isArray(workflowData?.connections) ? workflowData.connections : [];
        const resolvedConns = [];

        rawConns.forEach(c => {
            const src = this.workflow.state.nodeIdMap[c.source] || c.source;
            const trg = this.workflow.state.nodeIdMap[c.target] || c.target;

            // Only add if both nodes actually exist
            if (document.getElementById(src) && document.getElementById(trg)) {
                resolvedConns.push({
                    id: c.id || `conn-${Date.now()}-${Math.random()}`,
                    source: src,
                    target: trg,
                    outputType: c.outputType || null,
                    sourceSide: c.sourceSide || 'right', // Restore sides for flowchart lines
                    targetSide: c.targetSide || 'left'
                });
            }
        });

        this.workflow.state.connections = resolvedConns;

        // 6. Final UI Update
        if (!this.workflow.connectionManager.connectionSvg) {
            this.workflow.connectionManager.setupConnections();
        }
        this.workflow.connectionManager.updateConnections();

        this.workflow.state.showInstructions = false;

        // Setup Fixed Nodes IDs state again (for Delete protection)
        setTimeout(() => this.workflow.setupFixedNodes(), 50);


    }



    verifyConnections(connections) {
        let validConnections = 0;
        let brokenConnections = 0;

        connections.forEach(conn => {
            const sourceExists = document.getElementById(conn.source);
            const targetExists = document.getElementById(conn.target);

            if (sourceExists && targetExists) {
                validConnections++;
            } else {
                brokenConnections++;
                console.error(`❌ Broken: ${conn.source} -> ${conn.target}`, {
                    sourceExists: !!sourceExists,
                    targetExists: !!targetExists
                });
            }
        });
    }

    async saveWorkflow() {
        // 1. Basic Validation (Empty Canvas)
        const nodes = Object.values(this.workflow.state.nodeConfigs);
        if (nodes.length === 0) {
            this.workflow.notification.add("Cannot save empty workflow", { type: 'warning' });
            return;
        }

        // 2. Get State
        const isNew = !this.state.workflowId;
        const isManual = this.workflow.state.workflowSettings.trigger_type === 'manual';

        // 3. INTERCEPTOR: If New + Manual, ask the user
        if (isNew && isManual) {
            this.workflow.dialog.add(ConfirmationDialog, {
                title: "Automation Not Configured",
                body: "Ready to set up when this workflow runs? You can add a schedule or event trigger, or leave it manual.",
                confirmLabel: "On a schedule",
                cancelLabel: "Manually only",
                confirm: () => {
                    // User chose to save anyway
                    this.workflow.openSettings();
                },
                cancel: async () => {
                    // User chose to configure -> Open Settings Panel
                    await this._handleNameAndSave();
                }
            });
            return; // Stop here, wait for dialog choice
        }

        // 4. Normal Save (Existing workflow OR Automation already set)
        await this._handleNameAndSave();
    }

    /**
     * Helper to handle the Naming Dialog and Execution
     */
    async _handleNameAndSave() {
        let existingId = this.state.workflowId;
        let workflowName = this.state.workflowName;

        if (existingId) {
            // Existing -> Save immediately
            await this._executeSave(existingId, workflowName);
        } else {
            // New -> Ask for Name first
            if (this.workflow.dialog) {
                // Assuming you have the WorkflowSaveDialog from previous steps
                this.workflow.dialog.add(WorkflowSaveDialog, {
                    defaultName: `Workflow-${new Date().toLocaleDateString()}`,
                    onConfirm: async (newName) => {
                        this.state.workflowName = newName;
                        await this._executeSave(null, newName);
                    }
                });
            } else {
                // Fallback
                const newName = prompt('Enter workflow name:', `Workflow-${new Date().toLocaleDateString()}`);
                if (newName) await this._executeSave(null, newName);
            }
        }
    }

    // --- HELPER: Performs the actual API Call ---
    async _executeSave(id, name) {
        try {
            // Use the centralized serialization method to ensure consistency (and Ghost Node injection)
            const serializedParams = this.serializeForSave();

            // Override ID/Name if provided (e.g. new save)
            if (id) serializedParams.id = id;
            if (name) serializedParams.name = name;

            // Prepare Payload for Odoo Backend
            const workflowData = {
                id: serializedParams.id,
                name: serializedParams.name,
                description: 'API Workflow created from workflow builder',
                workflow_data: JSON.stringify(serializedParams.workflow)
            };

            // Call Server
            const result = await this.orm.call('api.workflow', 'save_or_update_workflow', [workflowData]);

            if (result) {
                // Update State
                this.state.workflowId = result;

                // Draft Cleanup
                localStorage.removeItem('wb_draft_new');
                if (this.workflow.saveDraftNow) {
                    this.workflow.saveDraftNow();
                }

                // Update UI Buttons
                if (this.workflow.updateSaveButtonUI) {
                    this.workflow.lastSavedAt = new Date().toLocaleTimeString();
                    this.workflow.isDirty = false;
                    this.workflow.updateSaveButtonUI();
                }

                this.showNotification(
                    id ? `Workflow "${name}" updated successfully!` : `Workflow "${name}" created successfully!`,
                    'success'
                );
            }
        } catch (error) {
            console.error('❌ Error saving workflow:', error);
            this.showNotification(`Failed to save workflow: ${error.message}`, 'danger');
        }
    }

    serializeForSave() {
        // 1. Capture Visual Nodes (Start, End, API, etc.)
        const nodes = Object.values(this.workflow.state.nodeConfigs).map(n => ({
            id: n.id, type: n.type, x: n.x, y: n.y, config: n.config
        }));


        const settingsNode = {
            id: 'global_automation_settings',
            type: 'automation',
            config: { ...this.workflow.state.workflowSettings } // Clone current settings
        };
        nodes.push(settingsNode);



        // 3. Return Payload
        return {
            id: this.state.workflowId || null,
            name: this.state.workflowName || `Workflow-${new Date().toISOString()}`,
            workflow: {
                nodes, // Includes ghost node
                connections: this.state.connections || [],
                id_mapping: this.state.nodeIdMap || {},
                metadata: {
                    version: "1.0",
                    exportedAt: new Date().toISOString()
                }
            }
        };
    }
    // serializeForSave() {
    //     const nodes = Object.values(this.workflow.state.nodeConfigs || {}).map(n => ({
    //         id: n.id, type: n.type, x: n.x || 0, y: n.y || 0, config: n.config || {}
    //     }));
    //     return {
    //         id: this.state.workflowId || null,
    //         name: this.state.workflowName || `Workflow-${new Date().toISOString()}`,
    //         workflow: { nodes, connections: this.state.connections || [], id_mapping: this.state.nodeIdMap || {}, metadata: { exportedAt: new Date().toISOString() } }
    //     };
    // }

    async loadAutosaveDraft() {
        try {
            const res = await fetch('/api/workflows/autosave', { method: 'GET', credentials: 'same-origin', headers: { 'Accept': 'application/json' } });
            if (!res.ok) return null;
            const data = await res.json();
            if (!data || !data.workflow_data) return null;
            let wfObj;
            try { wfObj = JSON.parse(data.workflow_data); } catch (e) { wfObj = data.workflow_data; }
            await this.applyWorkflowFromObject(wfObj.workflow || wfObj);
            this.state.workflowId = data.id || this.state.workflowId;
            this.state.workflowName = data.name || this.state.workflowName;
            if (this.workflow) {
                this.workflow.isDirty = true;
                this.workflow.lastSavedAt = data.saved_at || new Date().toLocaleString();
                this.workflow.updateSaveButtonUI?.();
            }
            return data;
        } catch (e) {
            return null;
        }
    }

    async applyWorkflowFromObject(wf) {
        if (!wf) return;
        const nodes = wf.nodes || [];
        const connections = wf.connections || [];

        if (this.workflow.clearWorkflow) {
            await this.workflow.clearWorkflow();
        } else {
            this.state.nodeIdMap = {};
            this.state.nodeConfigs = {};
            this.state.connections = [];
            const elList = Array.from(document.querySelectorAll('.workflow-node'));
            elList.forEach(el => el.remove());
        }

        for (const n of nodes) {
            try {
                const newId = this.workflow.nodeManager.createWorkflowNode(n.type, n.x || 100, n.y || 100, n.id);
                if (this.state.nodeConfigs[newId]) this.state.nodeConfigs[newId].config = n.config || {};
            } catch (e) { }
        }

        for (const c of connections) {
            try {
                const src = this.state.nodeIdMap[c.source] || c.source;
                const trg = this.state.nodeIdMap[c.target] || c.target;
                if (document.getElementById(src) && document.getElementById(trg)) {
                    this.workflow.connectionManager.createConnection(src, trg, c.id || null);
                }
            } catch (e) { }
        }

        if (!this.workflow.connectionManager.connectionSvg) this.workflow.connectionManager.setupConnections();
        this.workflow.connectionManager.updateConnections();
        this.workflow.state.showInstructions = false;
        this.workflow.state.configUpdateCounter++;
    }


    showNotification(message, type = 'info') {
        // Use the service passed from the main component
        if (this.notification) {
            this.notification.add(message, { type: type });
        }
        // Fallback to workflow's notification if available
        else if (this.workflow && this.workflow.notification) {
            this.workflow.notification.add(message, { type: type });
        }
        // Last resort log (better than alert)
        else {
        }
    }

    importWorkflowData(workflowData) {
        try {
            this.loadWorkflowData(workflowData);
            this.notification.add("Workflow loaded successfully!", { type: 'success' });
        } catch (error) {
            console.error('❌ Error importing workflow data:', error);
            this.notification.add("Failed to load workflow data", { type: 'danger' });
        }
    }
    getResponseFields(responseData) {
        if (responseData === null || responseData === undefined) return [];

        const fields = [];


        // Helper function
        const extract = (data, prefix = '', depth = 0) => {
            if (depth > 5) return; // Prevent infinite recursion
            if (!data) return;

            // 1. Handle Array (Root or Nested)
            if (Array.isArray(data)) {
                if (data.length > 0) {
                    // For Odoo lists, we usually care about the first item structure
                    // If we are at root (prefix is empty), path is "[0]"
                    // If nested (prefix="lines"), path is "lines[0]"
                    const itemPrefix = prefix ? `${prefix}[0]` : '[0]';

                    fields.push({
                        path: itemPrefix,
                        label: `${prefix || 'Root'} (First Item)`,
                        type: 'object',
                        value: data[0]
                    });

                    // Recurse into the first item
                    extract(data[0], itemPrefix, depth + 1);
                } else {
                    fields.push({
                        path: prefix || '[]',
                        label: 'Empty List',
                        type: 'array',
                        value: []
                    });
                }
                return;
            }

            // 2. Handle Object
            if (typeof data === 'object') {
                Object.keys(data).forEach(key => {
                    const value = data[key];
                    const currentPath = prefix ? `${prefix}.${key}` : key;
                    const type = Array.isArray(value) ? 'array' : typeof value;

                    // Add the field entry
                    fields.push({
                        path: currentPath,
                        label: currentPath,
                        type: type,
                        value: value
                    });

                    // Recurse if it's a nested object (not null)
                    if (type === 'object' && value !== null) {
                        extract(value, currentPath, depth + 1);
                    }
                    else if (Array.isArray(value) && value.length > 0) {
                        extract(value, currentPath, depth + 1);
                    }
                });
            }
        };

        extract(responseData);

        return fields.sort((a, b) => a.path.localeCompare(b.path));
    }


    getFieldValue(nodeId, dataPath) {
        const responseData = this.getNodeResponseData(nodeId);
        if (!responseData || !dataPath) return null;

        return this.extractValueFromResponse(responseData, dataPath);
    }

    extractValueFromResponse(responseData, jsonPath) {
        if (!responseData || !jsonPath) return null;

        try {
            if (!jsonPath.includes('.') && !jsonPath.includes('[')) {
                return responseData[jsonPath] !== undefined ? responseData[jsonPath] : null;
            }

            if (jsonPath.includes('[*]')) {
                const pathParts = jsonPath.split('[*]');
                const arrayPath = pathParts[0];
                const remainingPath = pathParts.slice(1).join('').replace(/^\./, '');

                let current = responseData;

                if (arrayPath) {
                    const arrayPathParts = arrayPath.split('.');
                    for (const part of arrayPathParts) {
                        if (current && typeof current === 'object' && part in current) {
                            current = current[part];
                        } else {
                            return null;
                        }
                    }
                }

                if (Array.isArray(current) && current.length > 0) {
                    current = current[0];

                    if (remainingPath) {
                        const remainingParts = remainingPath.split('.');
                        for (const part of remainingParts) {
                            if (current && typeof current === 'object' && part in current) {
                                current = current[part];
                            } else {
                                return null;
                            }
                        }
                    }

                    return current;
                }
                return null;
            }

            const pathParts = jsonPath.split('.');
            let current = responseData;

            for (const part of pathParts) {
                if (current === null || current === undefined) return null;

                const arrayMatch = part.match(/(\w+)\[(\d+)\]/);
                if (arrayMatch && current) {
                    const arrayName = arrayMatch[1];
                    const arrayIndex = parseInt(arrayMatch[2]);

                    if (current[arrayName] && Array.isArray(current[arrayName]) &&
                        current[arrayName].length > arrayIndex) {
                        current = current[arrayName][arrayIndex];
                    } else {
                        return null;
                    }
                }
                else if (part.startsWith('[') && part.endsWith(']')) {
                    const arrayIndex = parseInt(part.slice(1, -1));
                    if (Array.isArray(current) && current.length > arrayIndex) {
                        current = current[arrayIndex];
                    } else {
                        return null;
                    }
                }
                else if (current && typeof current === 'object' && part in current) {
                    current = current[part];
                } else {
                    return null;
                }
            }

            return current;
        } catch (error) {
            console.error('Error extracting value from response:', error, { jsonPath, responseData });
            return null;
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



    getInputConnectedNode(nodeId) {
        if (!this.state.connections) return null;

        const inputConnections = this.state.connections.filter(conn => conn.target === nodeId);
        return inputConnections.length > 0 ? inputConnections[0].source : null;
    }

    getConnectionInfo(nodeId) {
        if (!this.state.connections) return { inputConnections: [], outputConnections: [] };

        const inputConnections = this.state.connections.filter(conn => conn.target === nodeId);
        const outputConnections = this.state.connections.filter(conn => conn.source === nodeId);

        const enhancedInputConnections = inputConnections.map(conn => ({
            ...conn,
            sourceType: this.state.nodeConfigs[conn.source]?.type || 'unknown'
        }));

        const enhancedOutputConnections = outputConnections.map(conn => ({
            ...conn,
            targetType: this.state.nodeConfigs[conn.target]?.type || 'unknown'
        }));

        return {
            inputConnections: enhancedInputConnections,
            outputConnections: enhancedOutputConnections,
            hasInput: inputConnections.length > 0,
            hasOutput: outputConnections.length > 0,
            totalConnections: inputConnections.length + outputConnections.length
        };
    }


    getBranchingInfo() {
        if (!this.state.workflowTestResults || !this.state.connections) {
            return { activeBranches: [], conditionResults: [] };
        }

        const activeBranches = [];
        const conditionResults = [];
        const nodeResults = this.state.workflowTestResults.results || [];

        this.state.connections.forEach(conn => {
            const sourceNodeResult = nodeResults.find(nr => nr.node_id === conn.source);

            if (sourceNodeResult && sourceNodeResult.node_type === 'condition') {
                const conditionResult = sourceNodeResult.condition_result;
                const outputType = conn.outputType;

                const isActive = (outputType === 'true' && conditionResult === true) ||
                    (outputType === 'false' && conditionResult === false) ||
                    !outputType || !['true', 'false'].includes(outputType);

                activeBranches.push({
                    source: conn.source,
                    target: conn.target,
                    outputType: outputType,
                    conditionResult: conditionResult,
                    isActive: isActive,
                    wasExecuted: isActive
                });

                if (!conditionResults.find(cr => cr.nodeId === conn.source)) {
                    conditionResults.push({
                        nodeId: conn.source,
                        result: conditionResult,
                        trueBranches: this.state.connections.filter(c =>
                            c.source === conn.source && c.outputType === 'true'
                        ).map(c => c.target),
                        falseBranches: this.state.connections.filter(c =>
                            c.source === conn.source && c.outputType === 'false'
                        ).map(c => c.target)
                    });
                }
            } else {
                activeBranches.push({
                    source: conn.source,
                    target: conn.target,
                    outputType: conn.outputType,
                    isActive: true,
                    wasExecuted: true
                });
            }
        });

        return { activeBranches, conditionResults };
    }

    isConnectionActive(connection) {
        if (!this.state.workflowTestResults) return true;

        const nodeResults = this.state.workflowTestResults.results || [];
        const sourceNodeResult = nodeResults.find(nr => nr.node_id === connection.source);

        if (sourceNodeResult && sourceNodeResult.node_type === 'condition') {
            const conditionResult = sourceNodeResult.condition_result;
            const outputType = connection.outputType;

            return (outputType === 'true' && conditionResult === true) ||
                (outputType === 'false' && conditionResult === false) ||
                !outputType || !['true', 'false'].includes(outputType);
        }

        return true;
    }

    getBranchExecutionSummary() {
        if (!this.state.workflowTestResults) return null;

        const nodeResults = this.state.workflowTestResults.results || [];
        const conditionNodes = nodeResults.filter(nr => nr.node_type === 'condition');

        let trueBranchesExecuted = 0;
        let falseBranchesExecuted = 0;

        conditionNodes.forEach(condition => {
            if (condition.condition_result === true) {
                trueBranchesExecuted++;
            } else {
                falseBranchesExecuted++;
            }
        });

        return {
            totalConditions: conditionNodes.length,
            trueBranchesExecuted,
            falseBranchesExecuted,
            branchesWithData: conditionNodes.filter(c => c.evaluation_details?.connected_node_data_used).length
        };
    }
    getConnectedNodeResponseData(conditionNodeId) {
        try {
            const connections = this.state.connections || [];
            const nodeConfig = this.state.nodeConfigs[conditionNodeId];

            if (nodeConfig?.config?.previousNodeId) {
                const manualNodeId = nodeConfig.config.previousNodeId;
                const responseData = this.getNodeResponseData(manualNodeId);
                if (responseData) {

                    return responseData;
                }
            }

            const inputConnections = connections.filter(conn => conn.target === conditionNodeId);
            for (const conn of inputConnections) {
                const responseData = this.getNodeResponseData(conn.source);
                if (responseData) {

                    return responseData;
                }
            }


            return null;
        } catch (error) {
            console.error('Error getting connected node response:', error);
            return null;
        }
    }
    getAvailablePreviousNodes(nodeId) {
        if (!this.state.nodeConfigs || !this.state.connections) {
            return [];
        }

        const previousNodes = [];
        const allNodeIds = Object.keys(this.state.nodeConfigs);

        allNodeIds.forEach(otherNodeId => {
            if (otherNodeId === nodeId) return;

            if (this.isNodeBefore(otherNodeId, nodeId)) {
                const otherNodeConfig = this.state.nodeConfigs[otherNodeId];
                const hasResponseData = !!this.getNodeResponseData(otherNodeId);

                previousNodes.push({
                    id: otherNodeId,
                    title: otherNodeConfig.title || `Node ${otherNodeId}`,
                    type: otherNodeConfig.type,
                    hasResponseData: hasResponseData,
                    isConnected: this.areNodesConnected(otherNodeId, nodeId)
                });
            }
        });

        return previousNodes.sort((a, b) => a.title.localeCompare(b.title));
    }
    isNodeBefore(nodeA, nodeB) {
        const connections = this.state.connections || [];

        const directConnection = connections.find(conn =>
            conn.source === nodeA && conn.target === nodeB
        );
        if (directConnection) return true;

        return true;
    }
    areNodesConnected(sourceId, targetId) {
        const connections = this.state.connections || [];
        return connections.some(conn =>
            conn.source === sourceId && conn.target === targetId
        );
    }
}