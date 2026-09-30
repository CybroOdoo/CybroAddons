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
            if (this._resizeDebounceTimer) {
                clearTimeout(this._resizeDebounceTimer);
            }
            this._resizeDebounceTimer = setTimeout(() => {
                this.updateConnections();
            }, 50);
        });

        this._resizeObserver.observe(this.canvasRef.el);

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
        if (!nodeElement) return;

        if (nodeElement.dataset.type === 'end') {
            this.workflow.notification.add("End nodes cannot have outgoing connections.", { type: 'warning' });
            return;
        }

        const isCondition = nodeElement.dataset.type === 'condition';

        if (!isCondition) {
            const existingOutput = this.state.connections.find(c => c.source === nodeId);
            if (existingOutput) {
                this.workflow.notification.add("This node already has an outgoing connection.", { type: 'warning' });
                document.body.style.cursor = '';
                document.body.style.userSelect = '';
                return;
            }
        }

        this.clearTempConnection();

        const rect = nodeElement.getBoundingClientRect();
        const canvasRect = this.workflow.canvasRef.el.getBoundingClientRect();

        const relTop = rect.top - canvasRect.top;
        const relLeft = rect.left - canvasRect.left;

        if (isCondition && outputType) {
            const outputPoint = nodeElement.querySelector(`.${outputType}-output`);
            if (outputPoint) {
                const pointRect = outputPoint.getBoundingClientRect();
                startX = pointRect.left - canvasRect.left + pointRect.width / 2;
                startY = pointRect.top - canvasRect.top + pointRect.height / 2;
                side = 'right';
            }
        } else {
            switch (side) {
                case 'top': startX = relLeft + rect.width / 2; startY = relTop; break;
                case 'bottom': startX = relLeft + rect.width / 2; startY = relTop + rect.height; break;
                case 'left': startX = relLeft; startY = relTop + rect.height / 2; break;
                case 'right':
                default: startX = relLeft + rect.width; startY = relTop + rect.height / 2; break;
            }
        }

        this.state.tempConnection = {
            sourceNode: nodeId,
            sourceSide: side,
            outputType: outputType,
            startX: startX,
            startY: startY,
            x: startX,
            y: startY,
            active: true
        };

        if (side) {
            const point = nodeElement.querySelector(`.connection-point.${side}`);
            if (point) point.classList.add('connecting');
        } else if (outputType) {
            const point = nodeElement.querySelector(`.${outputType}-output`);
            if (point) point.classList.add('connecting');
        }

        this.workflow.canvasRef.el.classList.add('connection-mode');

        this.boundDrawTempConnection = this.drawTempConnection.bind(this);
        document.addEventListener('mousemove', this.boundDrawTempConnection);

        this.boundFinishConnection = this.finishConnection.bind(this);
        document.addEventListener('mouseup', this.boundFinishConnection);

        this.boundCancelConnection = this.cancelConnection.bind(this);
        document.addEventListener('keydown', this.boundCancelConnection);
    }

    updateTempConnectionPosition() {
        if (!this.state.tempConnection) return;
        const sn = document.getElementById(this.state.tempConnection.sourceNode);
        if (!sn) return;

        const canvasRect = this.canvasRef.el.getBoundingClientRect();
        const outputType = this.state.tempConnection.outputType;

        if (sn.dataset.type === 'condition' && outputType) {
            const op = sn.querySelector(`.${outputType}-output`);
            if (op) {
                const pr = op.getBoundingClientRect();
                this.state.tempConnection.startX = pr.left - canvasRect.left + pr.width / 2;
                this.state.tempConnection.startY = pr.top - canvasRect.top + pr.height / 2;
                return;
            }
        }

        const nr = sn.getBoundingClientRect();
        const side = this.state.tempConnection.sourceSide || 'right';

        switch (side) {
            case 'top': this.state.tempConnection.startX = nr.left - canvasRect.left + nr.width / 2; this.state.tempConnection.startY = nr.top - canvasRect.top; break;
            case 'bottom': this.state.tempConnection.startX = nr.left - canvasRect.left + nr.width / 2; this.state.tempConnection.startY = nr.top - canvasRect.top + nr.height; break;
            case 'left': this.state.tempConnection.startX = nr.left - canvasRect.left; this.state.tempConnection.startY = nr.top - canvasRect.top + nr.height / 2; break;
            case 'right':
            default: this.state.tempConnection.startX = nr.left - canvasRect.left + nr.width; this.state.tempConnection.startY = nr.top - canvasRect.top + nr.height / 2; break;
        }
    }

    drawTempConnection(ev) {
        if (!this.state.tempConnection) return;
        const rect = this.canvasRef.el.getBoundingClientRect();
        this.state.tempConnection.x = ev.clientX - rect.left;
        this.state.tempConnection.y = ev.clientY - rect.top;
        this.updateConnections();
    }

    finishConnection(ev) {
        if (!this.state.tempConnection) return;
        const targetNode = this.findNodeAtPosition(ev.clientX, ev.clientY);

        if (!targetNode || !this.isValidConnection(this.state.tempConnection.sourceNode, targetNode.id)) {
            this.clearTempConnection();
            return;
        }

        const tr = targetNode.getBoundingClientRect();
        const relX = ev.clientX - tr.left;
        const relY = ev.clientY - tr.top;
        const w = tr.width;
        const h = tr.height;

        let targetSide = 'left';
        if (relX / w > relY / h) {
            if (relX / w > (h - relY) / h) targetSide = 'right';
            else targetSide = 'top';
        } else {
            if (relX / w > (h - relY) / h) targetSide = 'bottom';
            else targetSide = 'left';
        }

        if (this.state.connections.some(c => c.target === targetNode.id)) {
            this.workflow.notification.add("Target node already has an input.", { type: 'warning' });
            this.clearTempConnection();
            return;
        }

        this.createConnection(
            this.state.tempConnection.sourceNode,
            targetNode.id,
            this.state.tempConnection.sourceSide,
            targetSide,
            this.state.tempConnection.outputType
        );

        this.clearTempConnection();
    }

    findNodeAtPosition(x, y) {
        const nodes = document.querySelectorAll('.workflow-node');
        for (const node of nodes) {
            const rect = node.getBoundingClientRect();
            if (x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom) {
                return node;
            }
        }
        return null;
    }

    refreshConnectedDots() {
        document.querySelectorAll('.connection-point').forEach(dot => dot.classList.remove('connected'));
        this.state.connections.forEach(conn => {
            const sn = document.getElementById(conn.source);
            const tn = document.getElementById(conn.target);
            if (sn) {
                if (conn.outputType && (conn.outputType === 'true' || conn.outputType === 'false')) {
                    const so = sn.querySelector(`.${conn.outputType}-output`);
                    if (so) so.classList.add('connected');
                } else if (conn.sourceSide) {
                    const dot = sn.querySelector(`.connection-point.${conn.sourceSide}`);
                    if (dot) dot.classList.add('connected');
                }
            }
            if (tn && conn.targetSide) {
                const dot = tn.querySelector(`.connection-point.${conn.targetSide}`);
                if (dot) dot.classList.add('connected');
            }
        });
    }

    createConnection(sourceNodeId, targetNodeId, sourceSide = 'right', targetSide = 'left', outputType = null) {
        const connection = {
            id: `conn-${Date.now()}`,
            source: sourceNodeId,
            target: targetNodeId,
            sourceSide: sourceSide,
            targetSide: targetSide,
            outputType: outputType || sourceSide
        };
        this.state.connections.push(connection);
        this.updateConnections();
        this.workflow.queueDraftSave();
    }

    updateConnections() {
        if (!this.connectionSvg) this.setupConnections();
        this.connectionSvg.innerHTML = '';

        const executed = new Set((this.workflow.state.executedConnections || [])
            .map(c => `${c.source}->${c.target}`));

        this.state.connections.forEach(conn => {
            const s = document.getElementById(conn.source);
            const t = document.getElementById(conn.target);
            if (!s || !t) return;

            const path = this.drawConnectionLine(s, t, false, conn.id);
            if (!path) return;

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

            if (isSelected) {
                const mid = this.getConnectionMidpoint(s, t);
                const g = document.createElementNS("http://www.w3.org/2000/svg", "g");
                g.setAttribute("transform", `translate(${mid.x}, ${mid.y})`);
                g.style.cursor = "pointer";
                g.style.pointerEvents = "auto";

                const bg = document.createElementNS("http://www.w3.org/2000/svg", "circle");
                bg.setAttribute("r", "14");
                bg.setAttribute("fill", "#212529");
                bg.setAttribute("stroke", "#4b5563");
                bg.setAttribute("stroke-width", "1");
                g.appendChild(bg);

                const icon = document.createElementNS("http://www.w3.org/2000/svg", "path");
                icon.setAttribute("d", "M-5 -6 L5 -6 L5 -8 L-5 -8 Z M-4 -6 L-4 7 L4 7 L4 -6 Z M-1 -4 L-1 5 M1 -4 L1 5");
                icon.setAttribute("fill", "none");
                icon.setAttribute("stroke", "#9ca3af");
                icon.setAttribute("stroke-width", "1.5");
                icon.setAttribute("stroke-linecap", "round");
                g.appendChild(icon);

                g.addEventListener("mouseenter", () => { bg.setAttribute("stroke", "#ef4444"); icon.setAttribute("stroke", "#ef4444"); });
                g.addEventListener("mouseleave", () => { bg.setAttribute("stroke", "#4b5563"); icon.setAttribute("stroke", "#9ca3af"); });
                g.addEventListener("click", (e) => {
                    e.stopPropagation();
                    this.removeConnection(conn.id);
                });
                this.connectionSvg.appendChild(g);
            }
        });

        if (this.state.tempConnection) {
            this.updateTempConnectionPosition();
            const sn = document.getElementById(this.state.tempConnection.sourceNode);
            if (sn) {
                const tp = this.drawConnectionLine(sn, null, true, 'temp');
                if (tp) {
                    tp.setAttribute('stroke', '#007bff');
                    tp.setAttribute('stroke-width', '2');
                    tp.setAttribute('stroke-dasharray', '5,5');
                    tp.style.opacity = '0.7';
                }
            }
        }
        this.refreshConnectedDots();
    }

    getConnectionMidpoint(sourceEl, targetEl) {
        const cr = this.canvasRef.el.getBoundingClientRect();
        const s = sourceEl.getBoundingClientRect();
        const t = targetEl ? targetEl.getBoundingClientRect() : { left: this.state.tempConnection.x + cr.left, top: this.state.tempConnection.y + cr.top, width: 0, height: 0 };

        const x1 = s.right - cr.left;
        const y1 = s.top + s.height / 2 - cr.top;
        const x2 = t.left - cr.left;
        const y2 = t.top + t.height / 2 - cr.top;

        return { x: (x1 + x2) / 2, y: (y1 + y2) / 2 - 10 };
    }

    drawConnectionLine(source, target, isTemp = false, connectionId = '') {
        const cr = this.canvasRef.el.getBoundingClientRect();
        let sx, sy, tx, ty;
        let ss = 'right', ts = 'left';

        if (isTemp) {
            sx = this.state.tempConnection.startX;
            sy = this.state.tempConnection.startY;
            ss = this.state.tempConnection.sourceSide || 'right';
            tx = this.state.tempConnection.x;
            ty = this.state.tempConnection.y;
            const dx = tx - sx, dy = ty - sy;
            if (Math.abs(dx) > Math.abs(dy)) ts = dx > 0 ? 'left' : 'right';
            else ts = dy > 0 ? 'top' : 'bottom';
        } else {
            const conn = this.state.connections.find(c => c.id === connectionId);
            ss = conn.sourceSide || 'right';
            ts = conn.targetSide || 'left';
            const getC = (el, side, ot) => {
                const r = el.getBoundingClientRect();
                if (el.dataset.type === 'condition' && ot) {
                    const so = el.querySelector(`.${ot}-output`);
                    if (so) { const pr = so.getBoundingClientRect(); return { x: pr.left - cr.left + pr.width / 2, y: pr.top - cr.top + pr.height / 2 }; }
                }
                const tp = r.top - cr.top, lf = r.left - cr.left;
                switch (side) {
                    case 'top': return { x: lf + r.width / 2, y: tp };
                    case 'bottom': return { x: lf + r.width / 2, y: tp + r.height };
                    case 'left': return { x: lf, y: tp + r.height / 2 };
                    case 'right': default: return { x: lf + r.width, y: tp + r.height / 2 };
                }
            };
            const sc = getC(source, ss, conn.outputType), tc = getC(target, ts, null);
            sx = sc.x; sy = sc.y; tx = tc.x; ty = tc.y;
        }

        let d = "";
        const r = 15;
        if (Math.abs(sx - tx) < 20 && Math.abs(sy - ty) < 20) d = `M ${sx} ${sy} L ${tx} ${ty}`;
        else {
            if ((ss === 'right' || ss === 'left') && (ts === 'left' || ts === 'right')) {
                const mx = sx + (tx - sx) / 2;
                const dy = ty > sy ? 1 : -1;
                const radius = Math.min(r, Math.abs(ty - sy) / 2, Math.abs(mx - sx));
                d = `M ${sx} ${sy} L ${mx - (radius * (tx > sx ? 1 : -1))} ${sy} Q ${mx} ${sy} ${mx} ${sy + (radius * dy)} L ${mx} ${ty - (radius * dy)} Q ${mx} ${ty} ${mx + (radius * (tx > sx ? 1 : -1))} ${ty} L ${tx} ${ty}`;
            } else if ((ss === 'top' || ss === 'bottom') && (ts === 'top' || ts === 'bottom')) {
                const my = sy + (ty - sy) / 2;
                const dx = tx > sx ? 1 : -1;
                const radius = Math.min(r, Math.abs(tx - sx) / 2, Math.abs(my - sy));
                d = `M ${sx} ${sy} L ${sx} ${my - (radius * (ty > sy ? 1 : -1))} Q ${sx} ${my} ${sx + (radius * dx)} ${my} L ${tx - (radius * dx)} ${my} Q ${tx} ${my} ${tx} ${my + (radius * (ty > sy ? 1 : -1))} L ${tx} ${ty}`;
            } else {
                const radius = Math.min(r, Math.abs(tx - sx), Math.abs(ty - sy));
                if (ss === 'left' || ss === 'right') {
                    const dx = tx > sx ? 1 : -1;
                    d = `M ${sx} ${sy} L ${tx - (radius * dx)} ${sy} Q ${tx} ${sy} ${tx} ${sy + (radius * (ty > sy ? 1 : -1))} L ${tx} ${ty}`;
                } else {
                    const dy = ty > sy ? 1 : -1;
                    d = `M ${sx} ${sy} L ${sx} ${ty - (radius * dy)} Q ${sx} ${ty} ${sx + (radius * (tx > sx ? 1 : -1))} ${ty} L ${tx} ${ty}`;
                }
            }
        }
        const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        p.setAttribute('d', d); p.setAttribute('fill', 'none'); p.setAttribute('stroke-linejoin', 'round'); p.setAttribute('stroke-linecap', 'round');
        if (connectionId) p.setAttribute('data-id', connectionId);
        this.connectionSvg.appendChild(p);
        return p;
    }

    removeConnection(connectionId) {
        this.workflow.state.connections = this.workflow.state.connections.filter(c => c.id !== connectionId);
        if (this.selectedConnectionId === connectionId) this.selectedConnectionId = null;
        this.updateConnections();
        this.workflow.state.configUpdateCounter++;
        if (this.workflow.queueDraftSave) this.workflow.queueDraftSave();
    }

    clearTempConnection() {
        document.body.style.userSelect = '';
        document.body.style.cursor = '';
        if (this.state.tempConnection) {
            const sn = document.getElementById(this.state.tempConnection.sourceNode);
            if (sn) {
                let s;
                if (sn.dataset.type === 'condition' && this.state.tempConnection.outputType) s = `.${this.state.tempConnection.outputType}-output`;
                else s = this.state.tempConnection.isOutput ? '.connection-point.output' : '.connection-point.input';
                const cp = sn.querySelector(s);
                if (cp) cp.classList.remove('connecting');
            }
            this.workflow.canvasRef.el.classList.remove('connection-mode');
            window.removeEventListener('mousemove', this.handleMouseMove);
            window.removeEventListener('mouseup', this.handleMouseUp);
        }
        this.state.tempConnection = null;
    }

    cancelConnection(event) {
        if (event.key === 'Escape' && this.state.tempConnection) this.clearTempConnection();
    }

    isValidConnection(sId, tId) {
        const sn = document.getElementById(sId), tn = document.getElementById(tId);
        if (!sn || !tn) return false;
        if (sId === tId) { this.workflow.notification.add("A node cannot connect to itself.", { type: 'warning' }); return false; }
        if (sn.dataset.type === 'end') { this.workflow.notification.add("End nodes cannot have outgoing connections.", { type: 'warning' }); return false; }
        if (tn.dataset.type === 'start') { this.workflow.notification.add("Start nodes cannot have incoming connections.", { type: 'warning' }); return false; }
        return true;
    }
}