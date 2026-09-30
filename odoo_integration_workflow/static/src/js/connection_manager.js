/** @odoo-module **/

export class ConnectionManager {
    constructor(workflowBuilder) {
        this.workflow = workflowBuilder;
        this.state = workflowBuilder.state;
        this.canvasRef = workflowBuilder.canvasRef;
        this.connectionSvg = null;
    }

    setupConnections() {
        const existingSvg = this.canvasRef.el.querySelector('.connections-layer');
        if (existingSvg) {
            existingSvg.remove();
        }

        this.connectionSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        this.connectionSvg.setAttribute("class", "connections-layer");
        this.connectionSvg.style.position = "absolute";
        this.connectionSvg.style.top = "0";
        this.connectionSvg.style.left = "0";
        this.connectionSvg.style.width = "100%";
        this.connectionSvg.style.height = "100%";
        this.connectionSvg.style.pointerEvents = "none";
        this.connectionSvg.style.zIndex = "5";
        this.connectionSvg.setAttribute('width', '100%');
        this.connectionSvg.setAttribute('height', '100%');
        this.connectionSvg.style.overflow = "visible";
        this.selectedConnectionId = null;

        this.canvasRef.el.appendChild(this.connectionSvg);
        if (this._resizeObserver) {
            this._resizeObserver.disconnect();
        }

        this._resizeObserver = new ResizeObserver(() => {
            // ✅ Debounce: wait for the transition to finish before redrawing
            if (this._resizeDebounceTimer) {
                clearTimeout(this._resizeDebounceTimer);
            }
            this._resizeDebounceTimer = setTimeout(() => {
                this.updateConnections();
            }, 50); // 50ms is enough to let CSS transitions settle
        });

        this._resizeObserver.observe(this.canvasRef.el);

        // ✅ Remove the old window listener if it was previously attached
        if (this._resizeBound) {
            window.removeEventListener('resize', this._resizeBound);
            this._resizeBound = null;
        }
    }

    startConnection(nodeId, side, outputType = null) {
        let startX, startY;
        document.body.style.userSelect = 'none';
        document.body.style.cursor = 'crosshair';


        const nodeElement = document.getElementById(nodeId);
        if (!nodeElement) {
            console.error("Node element not found:", nodeId);
            return;
        }
        if (nodeElement.dataset.type === 'end') {
            this.workflow.notification.add("End nodes cannot have outgoing connections.", {type: 'warning'});
            return;
        }

        // -------------------------------------------------------------
        // 🛑 CONSTRAINT CHECK: 1 Output Per Node
        // -------------------------------------------------------------
        // Condition nodes allow multiple outputs (True/False).
        // Standard nodes only allow 1 outgoing connection.
        const isCondition = nodeElement.dataset.type === 'condition';

        if (!isCondition) {
            const existingOutput = this.state.connections.find(c => c.source === nodeId);
            if (existingOutput) {
                this.workflow.notification.add("This node already has an outgoing connection.", {type: 'warning'});
                // Reset cursor
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                return;
            }
        }

        this.clearTempConnection();

        const rect = nodeElement.getBoundingClientRect();
        const canvasElement = this.workflow.canvasRef.el;
        if (!canvasElement) return;

        const canvasRect = canvasElement.getBoundingClientRect();

        // Calculate coordinates relative to the canvas container
        const relTop = rect.top - canvasRect.top;
        const relLeft = rect.left - canvasRect.left;

        // -------------------------------------------------------------
        // 📐 COORDINATE CALCULATION
        // -------------------------------------------------------------
        if (isCondition && outputType) {
            // Legacy logic for Condition Node "True/False" buttons
            const outputPoint = nodeElement.querySelector(`.${outputType}-output`);
            if (outputPoint) {
                const pointRect = outputPoint.getBoundingClientRect();
                startX = pointRect.left - canvasRect.left + pointRect.width / 2;
                startY = pointRect.top - canvasRect.top + pointRect.height / 2;
                side = 'right'; // Force side for condition nodes
            }
        } else {
            // 4-Sided Logic for Standard Nodes
            switch (side) {
                case 'top':
                    startX = relLeft + rect.width / 2;
                    startY = relTop;
                    break;
                case 'bottom':
                    startX = relLeft + rect.width / 2;
                    startY = relTop + rect.height;
                    break;
                case 'left':
                    startX = relLeft;
                    startY = relTop + rect.height / 2;
                    break;
                case 'right':
                    startX = relLeft + rect.width;
                    startY = relTop + rect.height / 2;
                    break;
                default:
                    // Fallback
                    startX = relLeft + rect.width;
                    startY = relTop + rect.height / 2;
            }
        }

        // -------------------------------------------------------------
        // 💾 SAVE STATE
        // -------------------------------------------------------------
        this.state.tempConnection = {
            sourceNode: nodeId,
            sourceSide: side, // Important: We save which side we started from
            outputType: outputType,
            startX: startX,
            startY: startY,
            x: startX,
            y: startY,
            active: true
        };

        // Visual Feedback (Highlight the specific dot)
        if (side) {
            const point = nodeElement.querySelector(`.connection-point.${side}`);
            if (point) point.classList.add('connecting');
        } else if (outputType) {
            const point = nodeElement.querySelector(`.${outputType}-output`);
            if (point) point.classList.add('connecting');
        }

        this.workflow.canvasRef.el.classList.add('connection-mode');

        // Update Listeners
        this.boundDrawTempConnection = this.drawTempConnection.bind(this);
        document.addEventListener('mousemove', this.boundDrawTempConnection);

        this.boundFinishConnection = this.finishConnection.bind(this);
        // Changed to mouseup because drag-and-drop usually ends on mouse release
        document.addEventListener('mouseup', this.boundFinishConnection);

        this.boundCancelConnection = this.cancelConnection.bind(this);
        document.addEventListener('keydown', this.boundCancelConnection);
    }

    updateTempConnectionPosition() {
        if (!this.state.tempConnection) return;
        const nodeElement = document.getElementById(this.state.tempConnection.sourceNode);
        if (!nodeElement) return;

        const canvasRect = this.canvasRef.el.getBoundingClientRect();
        const outputType = this.state.tempConnection.outputType;

        if (nodeElement.dataset.type === 'condition' && (outputType === 'true' || outputType === 'false')) {
            const specificOutput = nodeElement.querySelector(`.${outputType}-output`);
            if (specificOutput) {
                const pointRect = specificOutput.getBoundingClientRect();
                this.state.tempConnection.startX = pointRect.left - canvasRect.left + pointRect.width / 2;
                this.state.tempConnection.startY = pointRect.top - canvasRect.top + pointRect.height / 2;
                return;
            }
        }

        const nodeRect = nodeElement.getBoundingClientRect();
        const side = this.state.tempConnection.sourceSide || 'right';

        switch (side) {
            case 'top':
                this.state.tempConnection.startX = nodeRect.left - canvasRect.left + nodeRect.width / 2;
                this.state.tempConnection.startY = nodeRect.top - canvasRect.top;
                break;
            case 'bottom':
                this.state.tempConnection.startX = nodeRect.left - canvasRect.left + nodeRect.width / 2;
                this.state.tempConnection.startY = nodeRect.top - canvasRect.top + nodeRect.height;
                break;
            case 'left':
                this.state.tempConnection.startX = nodeRect.left - canvasRect.left;
                this.state.tempConnection.startY = nodeRect.top - canvasRect.top + nodeRect.height / 2;
                break;
            case 'right':
            default:
                this.state.tempConnection.startX = nodeRect.left - canvasRect.left + nodeRect.width;
                this.state.tempConnection.startY = nodeRect.top - canvasRect.top + nodeRect.height / 2;
                break;
        }
    }

    drawTempConnection(ev) {
        if (!this.state.tempConnection) return;

        const canvas = this.canvasRef.el;
        const rect = canvas.getBoundingClientRect();
        this.state.tempConnection.x = ev.clientX - rect.left;
        this.state.tempConnection.y = ev.clientY - rect.top;

        this.updateConnections();
    }

    finishConnection(ev) {
        if (!this.state.tempConnection) return;

        const targetNode = this.findNodeAtPosition(ev.clientX, ev.clientY);

        // 1. Validation: If no node found or it's an invalid connection (like self-connect)
        if (!targetNode || !this.isValidConnection(this.state.tempConnection.sourceNode, targetNode.id)) {
            this.clearTempConnection();
            return;
        }

        // 2. Detect which side of target we are closest to (Define targetSide here)
        const targetRect = targetNode.getBoundingClientRect();
        const mouseX = ev.clientX;
        const mouseY = ev.clientY;
        const relX = mouseX - targetRect.left;
        const relY = mouseY - targetRect.top;
        const w = targetRect.width;
        const h = targetRect.height;

        let targetSide = 'left'; // Default
        if (relX / w > relY / h) {
            if (relX / w > (h - relY) / h) targetSide = 'right';
            else targetSide = 'top';
        } else {
            if (relX / w > (h - relY) / h) targetSide = 'bottom';
            else targetSide = 'left';
        }

        // 3. Enforce "One Input" Constraint
        const hasInput = this.state.connections.some(c => c.target === targetNode.id);
        if (hasInput) {
            this.workflow.notification.add("Target node already has an input.", {type: 'warning'});
            this.clearTempConnection();
            return;
        }

        // 4. Create Connection
        // Note: We pass sourceSide and targetSide. We need to update createConnection to accept them.
        this.createConnection(
            this.state.tempConnection.sourceNode,
            targetNode.id,
            this.state.tempConnection.sourceSide,
            targetSide,
            this.state.tempConnection.outputType // Pass through outputType (true/false)
        );

        this.clearTempConnection();
    }

    findNodeAtPosition(x, y) {
        const nodes = document.querySelectorAll('.workflow-node');

        for (const node of nodes) {
            const rect = node.getBoundingClientRect();

            const connectionPoints = node.querySelectorAll('.connection-point');
            let isNearConnectionPoint = false;

            connectionPoints.forEach(point => {
                const pointRect = point.getBoundingClientRect();
                if (x >= pointRect.left - 10 && x <= pointRect.right + 10 &&
                    y >= pointRect.top - 10 && y <= pointRect.bottom + 10) {
                    isNearConnectionPoint = true;
                }
            });

            if (x >= rect.left && x <= rect.right &&
                y >= rect.top && y <= rect.bottom) {
                return node;
            }
        }

        return null;
    }

    /**
     * Marks dots as "connected" in the DOM so CSS can keep them visible.
     */
    refreshConnectedDots() {
        // 1. Reset: Remove .connected from ALL dots
        const allDots = document.querySelectorAll('.connection-point');
        allDots.forEach(dot => dot.classList.remove('connected'));

        // 2. Loop through active connections
        this.state.connections.forEach(conn => {
            const sourceNode = document.getElementById(conn.source);
            const targetNode = document.getElementById(conn.target);

            // A. Mark Source Dot
            if (sourceNode) {
                // Logic for Condition Nodes (True/False outputs)
                if (conn.outputType && (conn.outputType === 'true' || conn.outputType === 'false')) {
                    const specificOutput = sourceNode.querySelector(`.${conn.outputType}-output`);
                    if (specificOutput) specificOutput.classList.add('connected');
                }
                // Logic for Standard Nodes (Top/Right/Bottom/Left)
                else if (conn.sourceSide) {
                    const dot = sourceNode.querySelector(`.connection-point.${conn.sourceSide}`);
                    if (dot) dot.classList.add('connected');
                }
            }

            // B. Mark Target Dot
            if (targetNode && conn.targetSide) {
                const dot = targetNode.querySelector(`.connection-point.${conn.targetSide}`);
                if (dot) dot.classList.add('connected');
            }
        });
    }

    createConnection(sourceNodeId, targetNodeId, sourceSide = 'right', targetSide = 'left', outputType = null) {

        const sourceExists = document.getElementById(sourceNodeId);
        const targetExists = document.getElementById(targetNodeId);

        if (!sourceExists || !targetExists) {
            this.workflow.notification.add("Cannot create connection - nodes not found", {type: 'danger'});
            return;
        }

        // Check if connection already exists
        const existingConnection = this.state.connections.find(conn =>
            conn.source === sourceNodeId && conn.target === targetNodeId && conn.outputType === outputType
        );

        if (existingConnection) {
            this.workflow.notification.add("Connection already exists", {type: 'warning'});
            return;
        }

        // Store the sides so updateConnections knows where to draw the line
        const connection = {
            id: `conn-${Date.now()}`,
            source: sourceNodeId,
            target: targetNodeId,
            sourceSide: sourceSide, // Store which side it starts from
            targetSide: targetSide, // Store which side it ends at
            outputType: outputType || sourceSide   // Use explicit outputType if provided, else fallback to sourceSide
        };

        this.state.connections.push(connection);

        this.updateConnections();
        this.workflow.queueDraftSave();
    }


    updateConnections() {
        if (!this.connectionSvg) this.setupConnections();

        // Clear existing lines
        this.connectionSvg.innerHTML = '';

        // 1. Logic to determine which lines are "Executed" (Green)
        // (Copying your existing logic for identifying active routes)
        const nodes = this.workflow.state.nodeConfigs || {};
        const hasCondition = Object.values(nodes).some(n => n && n.type === 'condition');
        let executed;

        if (hasCondition) {
            const mode = (this.workflow.state.uiPrefs && this.workflow.state.uiPrefs.edgeMode) || 'executed';
            if (mode === 'route_until_error' && this._buildRouteUntilErrorEdges) {
                const ordered = this._buildRouteUntilErrorEdges();
                executed = new Set(ordered.map(c => `${c.source}->${c.target}`));
            } else if (this._buildActiveRouteSetFallback) {
                executed = this._buildActiveRouteSetFallback();
            } else {
                executed = new Set();
            }
        } else {
            const fromState = new Set((this.workflow.state.executedConnections || [])
                .map(c => `${c.source}->${c.target}`));
            const fromFlow = this._buildExecutedConnectionSet ? this._buildExecutedConnectionSet() : new Set();
            executed = new Set([...fromState, ...fromFlow]);

            const tests = this.workflow.state.nodeTestResults || {};
            (this.state.connections || []).forEach(c => {
                if (tests[c.source]?.status === 'success') {
                    executed.add(`${c.source}->${c.target}`);
                }
            });
        }

        const conns = this.state.connections || [];

        // 2. Draw Real Connections
        conns.forEach(conn => {
            const s = document.getElementById(conn.source);
            const t = document.getElementById(conn.target);
            if (!s || !t) return;

            const path = this.drawConnectionLine(s, t, false, conn.id);
            if (!path) return;

            // Selection & Styling Logic
            const isSelected = (this.selectedConnectionId === conn.id);

            if (isSelected) {
                path.setAttribute('stroke-width', '4');
                path.style.setProperty('stroke', '#007bff', 'important');
                path.style.opacity = '1';
            } else if (executed.has(`${conn.source}->${conn.target}`)) {
                path.setAttribute('stroke-width', '3');
                path.style.setProperty('stroke', '#28a745', 'important');
                path.style.opacity = '1';
            } else {
                path.setAttribute('stroke-width', '2');
                path.style.setProperty('stroke', '#9aa6b2', 'important');
                path.style.opacity = '0.6';
            }

            path.style.cursor = "pointer";
            path.style.pointerEvents = "stroke";

            path.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectedConnectionId = (this.selectedConnectionId === conn.id) ? null : conn.id;
                this.updateConnections();
            });

            // Trash Can Logic (Dark Mode)
            if (isSelected) {
                const mid = this.getConnectionMidpoint(s, t);
                const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
                group.setAttribute("transform", `translate(${mid.x}, ${mid.y})`);
                group.style.cursor = "pointer";
                group.style.pointerEvents = "auto"; // Crucial for clicking

                const bg = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                bg.setAttribute("r", "14");
                bg.setAttribute("fill", "#212529");
                bg.setAttribute("stroke", "#4b5563");
                bg.setAttribute("stroke-width", "1");
                group.appendChild(bg);

                const icon = document.createElementNS("http://www.w3.org/2000/svg", "path");
                const trashPath = "M-5 -6 L5 -6 L5 -8 L-5 -8 Z M-4 -6 L-4 7 L4 7 L4 -6 Z M-1 -4 L-1 5 M1 -4 L1 5";
                icon.setAttribute("d", trashPath);
                icon.setAttribute("fill", "none");
                icon.setAttribute("stroke", "#9ca3af");
                icon.setAttribute("stroke-width", "1.5");
                icon.setAttribute("stroke-linecap", "round");
                icon.setAttribute("transform", "scale(1.1)");
                group.appendChild(icon);

                group.addEventListener("mouseenter", () => {
                    bg.setAttribute("stroke", "#ef4444");
                    icon.setAttribute("stroke", "#ef4444");
                });
                group.addEventListener("mouseleave", () => {
                    bg.setAttribute("stroke", "#4b5563");
                    icon.setAttribute("stroke", "#9ca3af");
                });
                group.addEventListener("click", (e) => {
                    e.stopPropagation();
                    e.preventDefault();
                    this.removeConnection(conn.id);
                });

                // Add "Press Delete" Hint
                const hint = document.createElementNS("http://www.w3.org/2000/svg", "text");
                hint.setAttribute("x", "0");
                hint.setAttribute("y", "25");
                hint.setAttribute("text-anchor", "middle");
                hint.setAttribute("fill", "#6c757d");
                hint.setAttribute("font-size", "10px");
                //                hint.textContent = "Press Delete";
                hint.style.pointerEvents = "none";
                group.appendChild(hint);

                this.connectionSvg.appendChild(group);
            }
        });

        // 3. Draw Temporary Connection (Dragging Line)
        if (this.state.tempConnection) {
            this.updateTempConnectionPosition(); // Ensure start coordinates are fresh
            const sn = document.getElementById(this.state.tempConnection.sourceNode);
            if (sn) {
                // Draw the line
                const tempPath = this.drawConnectionLine(sn, this.state.tempConnection, true, 'temp');

                // ✅ FIX: ADD STYLING TO MAKE IT VISIBLE
                if (tempPath) {
                    tempPath.setAttribute('stroke', '#007bff');   // Blue
                    tempPath.setAttribute('stroke-width', '2');   // Width
                    tempPath.setAttribute('stroke-dasharray', '5,5'); // Dashed line effect
                    tempPath.style.opacity = '0.7';
                    tempPath.style.pointerEvents = 'none'; // Don't block mouse events
                }
            }
        }
        this.refreshConnectedDots();
    }

    /**
     * Remove a connection by ID and refresh the canvas
     */
    removeConnection(connectionId) {

        // 1. Update the Global State by filtering out the specific connection
        this.workflow.state.connections = this.workflow.state.connections.filter(
            c => c.id !== connectionId
        );

        // 2. Clear the selection variable if the deleted line was selected
        if (this.selectedConnectionId === connectionId) {
            this.selectedConnectionId = null;
        }

        // 3. Redraw the canvas (The line will disappear)
        this.updateConnections();

        // 4. Trigger Auto-Save and UI updates
        this.workflow.state.configUpdateCounter++;

        // If your workflow builder has the draft save function exposed:
        if (this.workflow.queueDraftSave) {
            this.workflow.queueDraftSave();
        }
    }

    // === helper: build ordered route edges from Start → ... (true/false respected)
    _buildOrderedRouteEdges() {
        const nodes = this.workflow.state.nodeConfigs || {};
        const tests = this.workflow.state.nodeTestResults || {};
        const cond = this.workflow.state.conditionResults || {};
        const conns = this.state.connections || [];

        if (!nodes || !conns.length) return [];

        // find the Start node id
        const start = Object.keys(nodes).find(id => nodes[id]?.type === 'start');
        if (!start) return [];

        // index outgoing edges by source
        const outMap = new Map();
        for (const c of conns) {
            if (!outMap.has(c.source)) outMap.set(c.source, []);
            outMap.get(c.source).push(c);
        }

        const route = [];
        const visited = new Set();
        let current = start;

        // safety bounds to avoid loops
        for (let hop = 0; hop < conns.length + 5; hop++) {
            const outs = outMap.get(current) || [];
            if (!outs.length) break;

            let nextConn;

            const nCfg = nodes[current];
            if (nCfg?.type === 'condition') {
                // pick only the branch that actually evaluated
                const r = cond[current]?.result; // boolean true/false expected
                if (r === true) nextConn = outs.find(e => e.outputType === 'true');
                else if (r === false) nextConn = outs.find(e => e.outputType === 'false');
            }

            // non-condition or if missing branch info: pick a sensible next
            if (!nextConn) {
                // prefer an edge whose TARGET node succeeded, else first available
                nextConn = outs.find(e => tests[e.target]?.status === 'success') || outs[0];
            }

            if (!nextConn) break; // no way forward

            route.push(nextConn);

            // advance
            current = nextConn.target;
            if (visited.has(current)) break; // loop guard
            visited.add(current);

            // optional: stop if we reached an End node
            if (nodes[current]?.type === 'end') break;
        }

        return route;
    }

    _buildRouteUntilErrorEdges() {
        const nodes = this.workflow.state.nodeConfigs || {};
        const tests = this.workflow.state.nodeTestResults || {};
        const cond = this.workflow.state.conditionResults || {};
        const conns = this.state.connections || [];
        if (!conns.length) return [];

        const startId = Object.keys(nodes).find(id => nodes[id]?.type === 'start');
        if (!startId) return [];

        const out = new Map();
        for (const c of conns) {
            if (!out.has(c.source)) out.set(c.source, []);
            out.get(c.source).push(c);
        }

        const route = [];
        const visited = new Set();
        let cur = startId;

        for (let safety = 0; safety < conns.length + 5; safety++) {
            const outs = out.get(cur) || [];
            if (!outs.length) break;

            // choose next edge
            let next = null;
            if ((nodes[cur] || {}).type === 'condition') {
                const r = (cond[cur] || {}).result; // boolean true/false
                if (r === true) next = outs.find(e => e.outputType === 'true');
                if (r === false) next = outs.find(e => e.outputType === 'false');
            }
            // fallback: prefer an edge whose target succeeded; else take first
            if (!next) next = outs.find(e => tests[e.target]?.status === 'success') || outs[0];
            if (!next) break;

            route.push(next);
            cur = next.target;

            // stop at End or loop
            if ((nodes[cur] || {}).type === 'end') break;
            if (visited.has(cur)) break;
            visited.add(cur);

            // if target known and not success → stop after adding that edge
            const st = (tests[cur] || {}).status;
            if (st && st !== 'success') break;
        }
        return route;
    }

    //delete  line method
    getConnectionMidpoint(sourceEl, targetEl) {
        const canvasRect = this.canvasRef.el.getBoundingClientRect();
        const s = sourceEl.getBoundingClientRect();
        const t = targetEl.getBoundingClientRect();

        const x1 = s.right - canvasRect.left;
        const y1 = s.top + s.height / 2 - canvasRect.top;

        const x2 = t.left - canvasRect.left;
        const y2 = t.top + t.height / 2 - canvasRect.top;

        return {
            x: (x1 + x2) / 2,
            y: (y1 + y2) / 2 - 10
        };
    }


    drawConnectionLine(source, target, isTemp = false, connectionId = '') {
        // SAFETY CHECK
        if (!this.canvasRef || !this.canvasRef.el) return null;
        const canvasRect = this.canvasRef.el.getBoundingClientRect();

        let sourceX, sourceY, targetX, targetY;
        let sSide = 'right';
        let tSide = 'left';

        // -------------------------------------------------------------
        // 1. DETERMINE SIDES & COORDINATES
        // -------------------------------------------------------------

        // A. TEMP LINE (DRAGGING)
        if (isTemp) {
            // Start is fixed
            sourceX = this.state.tempConnection.startX;
            sourceY = this.state.tempConnection.startY;
            sSide = this.state.tempConnection.sourceSide || 'right';

            // Target is dynamic (Mouse Position)
            targetX = this.state.tempConnection.x;
            targetY = this.state.tempConnection.y;

            // Smart Target Side Calculation for Temp Line
            // (Guess the side based on angle relative to start)
            const dx = targetX - sourceX;
            const dy = targetY - sourceY;
            if (Math.abs(dx) > Math.abs(dy)) {
                tSide = dx > 0 ? 'left' : 'right';
            } else {
                tSide = dy > 0 ? 'top' : 'bottom';
            }
        }

        // B. SAVED LINE (STATIC)
        else {
            if (!source.getBoundingClientRect || !target.getBoundingClientRect) return null;

            const conn = this.state.connections.find(c => c.id === connectionId);
            if (conn) {
                sSide = conn.sourceSide || 'right';
                tSide = conn.targetSide || 'left';
            }

            // HELPER: Get Coords for a Specific Element/Side
            const getCoords = (el, side, outType) => {
                const r = el.getBoundingClientRect();
                const relTop = r.top - canvasRect.top;
                const relLeft = r.left - canvasRect.left;

                // SPECIAL LOGIC: CONDITION NODE OUTPUTS
                if (el.dataset.type === 'condition' && (outType === 'true' || outType === 'false')) {
                    const specificOutput = el.querySelector(`.${outType}-output`);
                    if (specificOutput) {
                        const pr = specificOutput.getBoundingClientRect();
                        // Condition dots are always on the right visually
                        return {
                            x: pr.left - canvasRect.left + pr.width / 2,
                            y: pr.top - canvasRect.top + pr.height / 2
                        };
                    }
                }

                // STANDARD 4-SIDED LOGIC
                switch (side) {
                    case 'top':    return { x: relLeft + r.width / 2, y: relTop };
                    case 'bottom': return { x: relLeft + r.width / 2, y: relTop + r.height };
                    case 'left':   return { x: relLeft, y: relTop + r.height / 2 };
                    case 'right':  return { x: relLeft + r.width, y: relTop + r.height / 2 };
                    default:       return { x: relLeft + r.width, y: relTop + r.height / 2 };
                }
            };

            const sCoords = getCoords(source, sSide, conn ? conn.outputType : null);
            const tCoords = getCoords(target, tSide, null);

            sourceX = sCoords.x;
            sourceY = sCoords.y;
            targetX = tCoords.x;
            targetY = tCoords.y;
        }

        // -------------------------------------------------------------
        // 2. DRAW PATH (SMOOTH STEPPED)
        // -------------------------------------------------------------

        let d = "";
        const cornerRadius = 15;

        // Fallback for extremely short distances (prevents loop glitches)
        if (Math.abs(sourceX - targetX) < 20 && Math.abs(sourceY - targetY) < 20) {
             d = `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`;
        }
        else {
            // Determine primary direction
            // Horizontal Flow (Left/Right)
            if ((sSide === 'right' || sSide === 'left') && (tSide === 'left' || tSide === 'right')) {
                const midX = sourceX + (targetX - sourceX) / 2;
                const dirY = targetY > sourceY ? 1 : -1;

                // Clamp radius if segments are too short
                const r = Math.min(cornerRadius, Math.abs(targetY - sourceY)/2, Math.abs(midX - sourceX));

                d = `M ${sourceX} ${sourceY} 
                     L ${midX - (r * (targetX>sourceX?1:-1))} ${sourceY} 
                     Q ${midX} ${sourceY} ${midX} ${sourceY + (r * dirY)} 
                     L ${midX} ${targetY - (r * dirY)} 
                     Q ${midX} ${targetY} ${midX + (r * (targetX>sourceX?1:-1))} ${targetY} 
                     L ${targetX} ${targetY}`;
            }
            // Vertical Flow (Top/Bottom)
            else if ((sSide === 'top' || sSide === 'bottom') && (tSide === 'top' || tSide === 'bottom')) {
                const midY = sourceY + (targetY - sourceY) / 2;
                const dirX = targetX > sourceX ? 1 : -1;

                const r = Math.min(cornerRadius, Math.abs(targetX - sourceX)/2, Math.abs(midY - sourceY));

                d = `M ${sourceX} ${sourceY}
                     L ${sourceX} ${midY - (r * (targetY>sourceY?1:-1))}
                     Q ${sourceX} ${midY} ${sourceX + (r * dirX)} ${midY}
                     L ${targetX - (r * dirX)} ${midY}
                     Q ${targetX} ${midY} ${targetX} ${midY + (r * (targetY>sourceY?1:-1))}
                     L ${targetX} ${targetY}`;
            }
            // Corner Flow (e.g. Bottom -> Right)
            else {
                // Simplified "L" shape with one curve for mixed axis
                const r = Math.min(cornerRadius, Math.abs(targetX - sourceX), Math.abs(targetY - sourceY));

                // Horizontal first, then Vertical? Or vice versa?
                // Logic: Move away from Source first
                if (sSide === 'left' || sSide === 'right') {
                     // Move X to Target X
                     const dirX = targetX > sourceX ? 1 : -1;
                     d = `M ${sourceX} ${sourceY} 
                          L ${targetX - (r * dirX)} ${sourceY} 
                          Q ${targetX} ${sourceY} ${targetX} ${sourceY + (r * (targetY>sourceY?1:-1))} 
                          L ${targetX} ${targetY}`;
                } else {
                     // Move Y to Target Y
                     const dirY = targetY > sourceY ? 1 : -1;
                     d = `M ${sourceX} ${sourceY} 
                          L ${sourceX} ${targetY - (r * dirY)} 
                          Q ${sourceX} ${targetY} ${sourceX + (r * (targetX>sourceX?1:-1))} ${targetY} 
                          L ${targetX} ${targetY}`;
                }
            }
        }

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-linecap', 'round');

        if (connectionId) path.setAttribute('data-id', connectionId);

        this.connectionSvg.appendChild(path);
        return path;
    }

    // Derive executed edges if backend data is missing/partial
    _buildActiveRouteSetFallback() {
        const conns = this.state.connections || [];
        const nodes = this.workflow.state.nodeConfigs || {};
        const tests = this.workflow.state.nodeTestResults || {};
        const condRes = this.workflow.state.conditionResults || {};

        const k = (s, t) => `${s}->${t}`;
        const set = new Set();

        // find a start node
        let startId = null;
        for (const id of Object.keys(nodes)) {
            if (nodes[id]?.type === 'start') {
                startId = id;
                break;
            }
        }
        if (!startId) return set;

        let current = startId, guard = 0;

        while (current && guard++ < 1000) {
            const cfg = nodes[current];
            if (!cfg) break;
            if (cfg.type === 'end') break;

            const outs = conns.filter(c => c.source === current);
            if (!outs.length) break;

            let next = null;

            if (cfg.type === 'condition') {
                const cr = condRes[current];
                const val = (cr && typeof cr.result === 'boolean') ? cr.result : null;
                if (val === true) next = outs.find(c => c.outputType === 'true') || null;
                if (val === false) next = outs.find(c => c.outputType === 'false') || null;
                if (!next) break;
            } else {
                // prefer an outgoing edge whose target node succeeded; else take single/first
                next = outs.find(c => tests[c.target]?.status === 'success') || (outs.length === 1 ? outs[0] : outs[0] || null);
                if (!next) break;
            }

            set.add(k(next.source, next.target));
            current = next.target;
        }

        return set;
    }


    // Build a set of "source->target" keys for the last executed flow
    _buildActiveRouteSet() {
        const conns = this.state.connections || [];
        const nodes = this.workflow.state.nodeConfigs || {};
        const results = this.workflow.state.nodeTestResults || {};
        const getCond = (id) =>
            (this.workflow.workflowIO.getConditionResult
                ? this.workflow.workflowIO.getConditionResult(id)
                : (this.workflow.state.conditionResults?.[id])) || null;

        const key = (s, t) => `${s}->${t}`;
        const out = new Set();

        // 1) find the Start node id
        let startId = null;
        for (const id of Object.keys(nodes)) {
            if (nodes[id]?.type === 'start') {
                startId = id;
                break;
            }
        }
        if (!startId) return out;

        // 2) walk from start → … → end using condition results and success markers
        let guard = 0;
        let current = startId;

        while (current && guard++ < 1000) {
            const currentCfg = nodes[current];
            if (!currentCfg) break;
            if (currentCfg.type === 'end') break;

            const outs = conns.filter(c => c.source === current);
            if (!outs.length) break;

            let nextEdge = null;

            if (currentCfg.type === 'condition') {
                // choose the branch that matches the evaluated condition
                const r = getCond(current);
                const condRes = (r && typeof r.result === 'boolean') ? r.result : null;
                if (condRes === true) {
                    nextEdge = outs.find(c => c.outputType === 'true') || null;
                } else if (condRes === false) {
                    nextEdge = outs.find(c => c.outputType === 'false') || null;
                } else {
                    // no result? give up (no highlight)
                    break;
                }
            } else {
                // prefer a target that actually succeeded in the last test
                nextEdge = outs.find(c => results[c.target]?.status === 'success')
                    || (outs.length === 1 ? outs[0] : null);
            }

            if (!nextEdge) break;

            out.add(key(nextEdge.source, nextEdge.target));
            current = nextEdge.target;
        }

        return out;
    }

    _buildExecutedConnectionSet() {
        const set = new Set();

        // get flow results captured after a test run
        const flows = (this.workflow.getFlowResults && this.workflow.getFlowResults()) || [];
        const allConns = this.state.connections || [];

        flows.forEach(flow => {
            // we prefer executed_nodes; if absent, try path
            const seq = Array.isArray(flow.executed_nodes) && flow.executed_nodes.length
                ? flow.executed_nodes
                : (Array.isArray(flow.path) ? flow.path : []);

            for (let i = 0; i < seq.length - 1; i++) {
                const s = seq[i];
                const t = seq[i + 1];

                // only mark if this exact edge exists in your graph
                const edge = allConns.find(c => c.source === s && c.target === t);
                if (edge) {
                    set.add(`${s}->${t}`);
                }
            }
        });

        return set;
    }


    getConnectionExecutionStatus(connection, flowResults) {
        if (!flowResults || flowResults.length === 0) return 'default';

        for (const flow of flowResults) {
            if (flow.executed_connections) {
                const wasExecuted = flow.executed_connections.some(conn =>
                    conn.source === connection.source && conn.target === connection.target
                );

                if (wasExecuted) {
                    return flow.success ? 'executed' : 'failed';
                }
            }
        }
        return 'default';
    }

    getConnectionTooltip(status) {
        const tooltips = {
            'executed': '✓ This connection was executed successfully',
            'failed': '✗ This connection was part of a failed flow',
            'default': 'Not executed in last test'
        };
        return tooltips[status] || '';
    }

    addExecutionIndicator(x, y, status) {
        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("cx", x);
        circle.setAttribute("cy", y);
        circle.setAttribute("r", "4");

        if (status === 'executed') {
            circle.setAttribute("fill", "#51cf66");
            circle.setAttribute("stroke", "#2b8a3e");
        } else if (status === 'failed') {
            circle.setAttribute("fill", "#ff6b6b");
            circle.setAttribute("stroke", "#c92a2a");
        }

        circle.setAttribute("stroke-width", "1");
        this.connectionSvg.appendChild(circle);
    }


    clearTempConnection() {
        document.body.style.userSelect = '';
        document.body.style.cursor = '';

        if (this.state.tempConnection) {
            const nodeElement = document.getElementById(this.state.tempConnection.sourceNode);
            if (nodeElement) {
                let selector;
                if (nodeElement.dataset.type === 'condition' && this.state.tempConnection.outputType) {
                    selector = `.${this.state.tempConnection.outputType}-output`;
                } else {
                    selector = this.state.tempConnection.isOutput ? '.connection-point.output' : '.connection-point.input';
                }
                const cp = nodeElement.querySelector(selector);
                if (cp) cp.classList.remove('connecting');
            }

            this.workflow.canvasRef.el.classList.remove('connection-mode');
            window.removeEventListener('mousemove', this.handleMouseMove);
            window.removeEventListener('mouseup', this.handleMouseUp);
        }

        this.state.tempConnection = null;
    }

    cancelConnection(event) {
        if (event.key === 'Escape' && this.state.tempConnection) {
            this.clearTempConnection();
        }
    }

    isValidConnection(sourceId, targetId) {
        const sourceNode = document.getElementById(sourceId);
        const targetNode = document.getElementById(targetId);

        if (!sourceNode || !targetNode) return false;

        // 1. Prevent self-connection
        if (sourceId === targetId) {
            this.workflow.notification.add("A node cannot connect to itself.", {type: 'warning'});
            return false;
        }

        const sourceType = sourceNode.dataset.type;
        const targetType = targetNode.dataset.type;

        // 2. Prevent outgoing from End
        if (sourceType === 'end') {
            this.workflow.notification.add("End nodes cannot have outgoing connections.", {type: 'warning'});
            return false;
        }

        // 3. Prevent incoming to Start
        if (targetType === 'start') {
            this.workflow.notification.add("Start nodes cannot have incoming connections.", {type: 'warning'});
            return false;
        }

        return true;
    }


}