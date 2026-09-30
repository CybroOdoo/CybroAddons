/** @odoo-module **/

import { NodeTemplates } from "./node_templates";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class NodeManager {
    constructor(workflowBuilder) {
        this.workflow = workflowBuilder;
        this.state = workflowBuilder.state;
        this.notification = workflowBuilder.notification;
        this.canvasRef = workflowBuilder.canvasRef;
        this.nodeTemplates = new NodeTemplates(workflowBuilder);
        this.generateUUID = workflowBuilder.generateUUID;
        this.loopManager = workflowBuilder.loopManager || null;
    }

    createWorkflowNode(type, x, y, originalId = null) {
        const nodeId = originalId || `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        if (!originalId) {
            this.workflow.addToHistory();
        }

        if (document.getElementById(nodeId)) {
            return nodeId;
        }

        const nodeElement = document.createElement('div');
        nodeElement.className = 'workflow-node';
        nodeElement.id = nodeId;
        nodeElement.style.left = `${x}px`;
        nodeElement.style.top = `${y}px`;
        nodeElement.dataset.type = type;

        // 1. Generate Connection Points (Keep your existing logic)
        let connectionPointsHTML = '';
        if (type === 'condition') {
            connectionPointsHTML = `
                <div class="connection-point input" data-side="left"></div>
                <div class="connection-points-output">
                    <div class="connection-point output true-output" data-output-type="true" title="True">T</div>
                    <div class="connection-point output false-output" data-output-type="false" title="False">F</div>
                </div>
            `;
        } else {
            connectionPointsHTML = `
                <div class="connection-point top" data-side="top"></div>
                <div class="connection-point right" data-side="right"></div>
                <div class="connection-point bottom" data-side="bottom"></div>
                <div class="connection-point left" data-side="left"></div>
            `;
        }

        // 2. Build HTML with INLINE BUTTON STYLES (No CSS file needed)
        // Clone on LEFT, Delete on RIGHT
        nodeElement.innerHTML = `
            <div style="position: absolute; top: -15px; right: 15px; z-index: 100;">
                <button class="btn-clone" title="Duplicate" 
                        style="width: 23px; height: 23px; border-radius: 50%; border: none; background: #3b82f6; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 12px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="23" height="23" viewBox="0 0 640 640"><path fill="currentColor" d="M352 512H128V288h48v-64h-48c-35.3 0-64 28.7-64 64v224c0 35.3 28.7 64 64 64h224c35.3 0 64-28.7 64-64v-48h-64zm-64-96h224c35.3 0 64-28.7 64-64V128c0-35.3-28.7-64-64-64H288c-35.3 0-64 28.7-64 64v224c0 35.3 28.7 64 64 64"/></svg>
                </button>
            </div>
            
            <div style="position: absolute; top: -15px; right: -10px; z-index: 100;">
                <button class="delete-node" title="Delete" 
                        style="width: 23px; height: 23px; border-radius: 50%; border: none; background: #ef4444; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 14px;">
                    ×
                </button>
            </div>

            ${connectionPointsHTML}

            <div class="node-header">
                <div class="node-icon">${this.nodeTemplates.getNodeIcon(type)}</div>
                <div class="node-title">${this.nodeTemplates.getNodeTitle(type)}</div>
            </div>
            ${type === 'loop' ? '<div class="node-status">Click to configure</div>' : ''}
            ${type === 'condition' ? '<div class="condition-badge">IF</div>' : ''}
        `;

        this.canvasRef.el.appendChild(nodeElement);

        // 3. Attach Listeners for Dots
        if (type !== 'condition') {
            const points = nodeElement.querySelectorAll('.connection-point');
            points.forEach(point => {
                point.addEventListener('mousedown', (e) => {
                    e.stopPropagation();
                    this.workflow.connectionManager.startConnection(nodeId, point.dataset.side);
                });
            });
        }

        // 4. Attach Events (Buttons)
        this.attachNodeEvents(nodeElement, nodeId);

        // 5. Finalize
        this.makeNodeDraggable(nodeElement);
        this.initializeNodeConfiguration(nodeId, type, x, y, originalId);
        this.updateNodeStatus(nodeId);
        this.workflow.queueDraftSave();

        return nodeId;
    }

    /**
     * Enhanced node configuration initialization
     * Handles both new nodes and imported nodes with existing configurations
     */
    initializeNodeConfiguration(nodeId, type, x, y, originalId = null) {

        if (this.state.nodeConfigs[nodeId]) {
            this.state.nodeConfigs[nodeId].x = x;
            this.state.nodeConfigs[nodeId].y = y;
        } else {
            const defaultConfig = this.nodeTemplates.getDefaultConfig(type);

            this.state.nodeConfigs[nodeId] = {
                id: nodeId,
                type: type,
                x: x,
                y: y,
                config: defaultConfig
            };

        }

        if (!this.state.workflowNodes.includes(nodeId)) {
            this.state.workflowNodes.push(nodeId);
        }
    }


    makeNodeDraggable(node) {
        let isDragging = false;
        let startX, startY, initialX, initialY;

        const dragMouseDown = (e) => {
            this.workflow.addToHistory();
            if (e.target.classList.contains('connection-point') ||
                e.target.classList.contains('delete-node')) {
                return;
            }

            e.preventDefault();
            e.stopPropagation();

            isDragging = true;
            startX = e.clientX;
            startY = e.clientY;

            // FIX 1: Use local coordinates instead of viewport coordinates
            initialX = node.offsetLeft;
            initialY = node.offsetTop;

            node.classList.add('dragging');
            document.addEventListener('mousemove', elementDrag);
            document.addEventListener('mouseup', closeDragElement);

            document.body.style.userSelect = 'none';
            document.body.style.cursor = 'grabbing';
        };

        const elementDrag = (e) => {
            if (!isDragging) return;
            e.preventDefault();

            // FIX 2: Account for Zoom Level
            const zoom = this.workflow.state.zoomLevel || 1;
            const deltaX = (e.clientX - startX) / zoom;
            const deltaY = (e.clientY - startY) / zoom;

            const newX = initialX + deltaX;
            const newY = initialY + deltaY;

            node.style.left = `${newX}px`;
            node.style.top = `${newY}px`;

            requestAnimationFrame(() => {
                this.workflow.connectionManager.updateConnections();
            });
        };

        const closeDragElement = () => {
            if (!isDragging) return;

            isDragging = false;
            node.classList.remove('dragging');
            document.removeEventListener('mousemove', elementDrag);
            document.removeEventListener('mouseup', closeDragElement);

            document.body.style.userSelect = '';
            document.body.style.cursor = '';

            if (this.state.nodeConfigs[node.id]) {
                this.state.nodeConfigs[node.id].x = parseInt(node.style.left);
                this.state.nodeConfigs[node.id].y = parseInt(node.style.top);
                this.workflow.queueDraftSave();
            }
        };

        node.addEventListener('mousedown', dragMouseDown);

        node.addEventListener('touchstart', (e) => {
            if (e.target.classList.contains('connection-point') ||
                e.target.classList.contains('delete-node')) {
                return;
            }

            e.preventDefault();
            isDragging = true;

            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;

            const rect = node.getBoundingClientRect();
            initialX = rect.left;
            initialY = rect.top;

            node.classList.add('dragging');
            document.addEventListener('touchmove', touchDrag);
            document.addEventListener('touchend', closeDragElement);
        });

        const touchDrag = (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const touch = e.touches[0];

            const deltaX = touch.clientX - startX;
            const deltaY = touch.clientY - startY;

            const newX = initialX + deltaX;
            const newY = initialY + deltaY;

            node.style.left = `${newX}px`;
            node.style.top = `${newY}px`;

            requestAnimationFrame(() => {
                this.workflow.connectionManager.updateConnections();
            });
        };
    }
    attachNodeEvents(nodeElement, nodeId) {
        nodeElement.addEventListener('click', (e) => {
            // Ignore clicks on connection points and action buttons
            if (e.target.classList.contains('connection-point') ||
                e.target.closest('.delete-node') ||
                e.target.closest('.btn-clone')) {
                return;
            }
            e.stopPropagation();
            this.workflow.selectNode(nodeId);
        });


        const deleteBtn = nodeElement.querySelector('.delete-node');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteNode(nodeId);
        });
        const cloneBtn = nodeElement.querySelector('.btn-clone');

        if (cloneBtn) {
            cloneBtn.addEventListener('click', (e) => {

                e.preventDefault(); // Add preventDefault just in case
                e.stopPropagation();
                this.cloneNode(nodeId);
            });
            // Add mousedown listener too, sometimes click is finicky with drag
            cloneBtn.addEventListener('mousedown', (e) => {
                e.stopPropagation();
            });
        }

        let trueOutput = null;
        let falseOutput = null;
        let inputPoint = null;
        let outputPoint = null;

        if (nodeElement.dataset.type === 'condition') {
            trueOutput = nodeElement.querySelector('.true-output');
            falseOutput = nodeElement.querySelector('.false-output');

            if (trueOutput) {
                trueOutput.addEventListener('mousedown', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.workflow.connectionManager.startConnection(nodeId, true, 'true');
                });
            }

            if (falseOutput) {
                falseOutput.addEventListener('mousedown', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.workflow.connectionManager.startConnection(nodeId, true, 'false');
                });
            }
        } else {
            inputPoint = nodeElement.querySelector('.connection-point.input');
            outputPoint = nodeElement.querySelector('.connection-point.output');

            if (inputPoint) {
                inputPoint.addEventListener('mousedown', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.workflow.connectionManager.startConnection(nodeId, false);
                });
            }

            if (outputPoint) {
                outputPoint.addEventListener('mousedown', (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.workflow.connectionManager.startConnection(nodeId, true);
                });
            }
        }



    }

    deleteNode(nodeId) {
        this.workflow.addToHistory();

        if (this.workflow.state.fixedNodes) {
            const fixedNodeIds = Object.values(this.workflow.state.fixedNodes);
            if (fixedNodeIds.includes(nodeId)) {
                this.workflow.notification.add("Cannot delete Start or End nodes", { type: 'warning' });
                return;
            }
        }
        const nodeElement = document.getElementById(nodeId);
        if (nodeElement) {
            nodeElement.remove();
        }

        this.state.workflowNodes = this.state.workflowNodes.filter(id => id !== nodeId);
        delete this.state.nodeConfigs[nodeId];

        this.state.connections = this.state.connections.filter(conn =>
            conn.source !== nodeId && conn.target !== nodeId
        );

        if (this.state.selectedNode === nodeId) {
            this.state.selectedNode = null;
        }

        this.workflow.connectionManager.updateConnections();
        this.workflow.queueDraftSave();
    }

    clearCanvas() {
        this.workflow.dialog.add(ConfirmationDialog, {
            title: "Clear Canvas",
            body: "Are you sure you want to clear the entire canvas? This action cannot be undone.",
            confirmLabel: "Clear Everything",
            cancelLabel: "Cancel",
            confirm: () => {
                // --- 1. Remove DOM Elements ---
                const canvas = this.workflow.canvasRef.el;
                Array.from(canvas.querySelectorAll('.workflow-node')).forEach(node => {
                    const nodeId = node.id;
                    if (this.workflow.state.fixedNodes &&
                        Object.values(this.workflow.state.fixedNodes).includes(nodeId)) {
                        return; // Skip fixed nodes
                    }
                    node.remove();
                });

                // --- 2. Rebuild State (Preserve Fixed Nodes) ---
                const fixedNodes = this.state.fixedNodes || {};
                const fixedNodeConfigs = {};
                const fixedWorkflowNodes = [];

                Object.values(fixedNodes).forEach(nodeId => {
                    if (this.state.nodeConfigs[nodeId]) {
                        fixedNodeConfigs[nodeId] = this.state.nodeConfigs[nodeId];
                        fixedWorkflowNodes.push(nodeId);
                    }
                });

                // --- 3. Reset Global State ---
                this.state.workflowNodes = fixedWorkflowNodes;
                this.state.nodeConfigs = fixedNodeConfigs;
                this.state.nodeIdCounter = 0;
                this.state.selectedNode = null;
                this.state.showInstructions = true;
                this.state.connections = [];

                // --- 4. Refresh UI ---
                this.workflow.connectionManager.updateConnections();

                // Optional: Show success notification
                this.workflow.notification.add("Canvas cleared successfully", { type: "success" });

                // Optional: Mark as draft dirty so autosave runs
                if (this.workflow.queueDraftSave) {
                    this.workflow.queueDraftSave();
                }
            },
            cancel: () => {
                // User clicked Cancel - do nothing
            }
        });
    }

    updateNodeStatus(nodeId) {
        const nodeConfig = this.state.nodeConfigs[nodeId];
        const element = document.getElementById(nodeId);
        // This will be null for most nodes now
        const statusDiv = element ? element.querySelector('.node-status') : null;

        if (!element) return;

        let isConfigured = false;
        let statusText = '';
        let statusClass = '';

        // 1. Handle Errors
        const nodeError = this.workflow.workflowIO?.getNodeError(nodeId);
        if (nodeError) {
            statusText = `Error: ${nodeError.message || nodeError.error}`;
            statusClass = 'node-error';

            // Visuals on Main Node (Border)
            element.classList.add('node-failed');
            element.classList.remove('node-configured');

            // Text Visuals (Only if box exists, e.g. Loop)
            if (statusDiv) {
                statusDiv.textContent = statusText;
                statusDiv.className = 'node-status ' + statusClass;
            }
            return;
        }

        // 2. Handle Test Results (Success/Fail)
        const testResult = this.workflow.getNodeResponse(nodeId);
        if (testResult && ['get', 'post', 'put', 'delete', 'orm'].includes(nodeConfig.type)) {
            if (testResult.success) {
                statusText = `✅ ${testResult.status_code || 'Success'}`;
                statusClass = 'node-success';
                element.classList.add('node-success-border'); // Optional CSS class for green border
            } else {
                statusText = `❌ ${testResult.status_code || 'Error'}`;
                statusClass = 'node-error';
            }
            isConfigured = true;
        }
        else {
            // 3. Handle Configuration State
            switch (nodeConfig.type) {
                case 'start':
                case 'end':
                    isConfigured = true;
                    break;
                case 'endpoint':
                    isConfigured = !!nodeConfig.config.baseUrl;
                    break;
                case 'auth':
                    isConfigured = nodeConfig.config.authType && nodeConfig.config.authType !== 'none';
                    if (nodeConfig.config.authType === 'basic') {
                        isConfigured = nodeConfig.config.username && nodeConfig.config.password;
                    } else if (nodeConfig.config.authType === 'bearer') {
                        isConfigured = !!nodeConfig.config.token;
                    } else if (nodeConfig.config.authType === 'api-key') {
                        isConfigured = !!nodeConfig.config.apiKey;
                    }
                    break;
                case 'get':
                case 'put':
                    isConfigured = !!nodeConfig.config.url;
                    // GET usually doesn't need body, strict check removed
                    break;
                case 'post':
                case 'delete':
                    isConfigured = !!nodeConfig.config.url;
                    break;
                case 'condition':
                    const hasLeft = nodeConfig.config.leftOperand;
                    const hasRight = nodeConfig.config.rightOperand;
                    isConfigured = hasLeft && hasRight;

                    const conditionResult = this.workflowIO?.getConditionResult(nodeId);
                    if (conditionResult) {
                        element.classList.add(conditionResult.result ? 'condition-true' : 'condition-false');
                    }
                    break;
                case 'loop':
                    // Keep detailed text for Loop
                    const loopStatus = this.loopManager.getLoopStatus(nodeId);
                    isConfigured = this.loopManager.validateLoopConfig(nodeId);
                    statusText = loopStatus;
                    statusClass = isConfigured ? 'node-success' : 'node-error';
                    break;
                case 'orm':
                    isConfigured = !!nodeConfig.config.model && !!nodeConfig.config.operation;
                    break;
            }
        }

        // 4. Update UI (Safely)
        if (statusDiv) {
            statusDiv.textContent = statusText || (isConfigured ? 'Ready' : 'Setup Needed');
            statusDiv.className = 'node-status ' + statusClass;
        }

        // Always update border styling
        element.classList.toggle('node-configured', isConfigured);
        element.classList.toggle('node-error', !isConfigured && nodeConfig.type !== 'start' && nodeConfig.type !== 'end');
        element.classList.toggle('node-failed', !!nodeError);
    }
    cloneNode(originalNodeId) {
        this.workflow.addToHistory();

        const originalNode = this.workflow.state.nodeConfigs[originalNodeId];
        const originalNodeConfig = this.workflow.state.nodeConfigs[originalNodeId];
        const originalEl = document.getElementById(originalNodeId);

        if (!originalNode || !originalEl) return;
        if (['start', 'end', 'automation'].includes(originalNodeConfig.type)) {
            this.workflow.notification.add("Cannot duplicate System nodes.", { type: 'warning' });
            return;
        }

        // Get Position
        const currentX = parseInt(originalEl.style.left) || 0;
        const currentY = parseInt(originalEl.style.top) || 0;

        // Shift Down & Right by 40px
        const newX = currentX + 40;
        const newY = currentY + 40;

        // Create New Node
        const newNodeId = this.createWorkflowNode(originalNode.type, newX, newY);

        // Copy Config (Deep Copy to break reference)
        if (this.workflow.state.nodeConfigs[newNodeId]) {
            const clonedConfig = JSON.parse(JSON.stringify(originalNode.config));
            this.workflow.state.nodeConfigs[newNodeId].config = clonedConfig;
        }

        // Feedback
        this.workflow.notification.add("Node duplicated", { type: 'success', timeout: 1000 });
        this.workflow.selectNode(newNodeId);
    }

    formatHttpResponse(response) {
        try {
            const statusClass = response.status_code >= 400 ? 'status-error' : 'status-success';
            return `
                <div class="http-response">
                    <div class="response-status ${statusClass}">
                        Status: ${response.status_code} ${response.message || ''}
                    </div>
                    <div class="response-time">
                        Response Time: ${response.response_time || 0}ms
                    </div>
                    <div class="response-headers">
                        <strong>Headers:</strong>
                        <pre>${JSON.stringify(response.headers || {}, null, 2)}</pre>
                    </div>
                    <div class="response-data">
                        <strong>Data:</strong>
                        <pre>${typeof response.data === 'object' ?
                    JSON.stringify(response.data, null, 2) :
                    response.data || 'No data'}</pre>
                    </div>
                </div>
            `;
        } catch (error) {
            return `Error displaying response: ${error.message}`;
        }
    }

    formatHttpError(error) {
        return `
            <div class="http-error">
                <div class="error-status status-error">
                    ❌ Request Failed
                </div>
                <div class="error-message">
                    <strong>Error:</strong> ${error.error || error.message || 'Unknown error'}
                </div>
                ${error.status_code ? `
                    <div class="error-code">
                        <strong>Status Code:</strong> ${error.status_code}
                    </div>
                ` : ''}
            </div>
        `;

    }
}