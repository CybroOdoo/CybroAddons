/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Layout } from "@web/search/layout";
import { Component, onMounted, onWillUnmount, onWillUpdateProps, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { _t } from "@web/core/l10n/translation";

export class WmRouteMapAction extends Component {
    static template = "wm_collection.WmRouteMap";
    static components = { Layout };

    setup() {
        this.action = useService("action");

        this.orm = useService("orm");
        this.notification = useService("notification");
        this.mapContainer = useRef("mapContainer");
        this.map = null;
        this.markers = [];
        this.polyline = null;
        this.routeId = this.props.action?.params?.route_id || this.props.action?.context?.active_id;

        this.state = useState({
            routeName: "",
            pointCount: 0,
            totalDistance: null,
            totalDuration: null,
        });

        onMounted(async () => {
            this.initMap();
            await this.loadRouteData();
        });

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
            }
        });
    }

    get display() {
        return {};
    }

    async onBackToRoute() {
        await this.action.restore();
    }

    initMap() {
        if (!this.mapContainer.el) return;

        // Initialize leaflet map
        this.map = L.map(this.mapContainer.el).setView([0, 0], 2);

        // Load street layer
        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(this.map);

        // Listen for popup open events to bind Add/Remove button click handlers
        this.map.on('popupopen', (e) => {
            const popupNode = e.popup.getElement();
            if (!popupNode) return;

            const addBtn = popupNode.querySelector('.js_add_to_route');
            if (addBtn) {
                addBtn.addEventListener('click', async (ev) => {
                    ev.preventDefault();
                    const pointId = parseInt(addBtn.dataset.pointId);
                    if (pointId) {
                        this.map.closePopup();
                        await this.addPointToRoute(pointId);
                    }
                });
            }

            const removeBtn = popupNode.querySelector('.js_remove_from_route');
            if (removeBtn) {
                removeBtn.addEventListener('click', async (ev) => {
                    ev.preventDefault();
                    const pointId = parseInt(removeBtn.dataset.pointId);
                    if (pointId) {
                        this.map.closePopup();
                        await this.removePointFromRoute(pointId);
                    }
                });
            }
        });
    }

    async loadRouteData() {
        const routeId = this.props.action?.params?.route_id || this.props.action?.context?.active_id;
        if (!routeId) return;
        this.routeId = routeId;

        try {
            const result = await this.orm.read("wm.route", [routeId], ["name", "estimated_duration", "route_map_data"]);
            if (result && result.length > 0) {
                this.state.routeName = result[0].name || "Route";
                if (result[0].estimated_duration) {
                    this.state.totalDuration = Math.round(result[0].estimated_duration * 60);
                }
                await this.updateMap(result[0].route_map_data);
            }
        } catch (error) {
            console.error("Failed to load route map data", error);
        }
    }

    async addPointToRoute(pointId) {
        if (!this.routeId || !pointId) return;
        try {
            await this.orm.call("wm.route", "action_add_collection_point", [[this.routeId], pointId]);
            if (this.notification) {
                this.notification.add(_t("Collection point added to route & Collection Order created!"), { type: "success" });
            }
            await this.loadRouteData();
        } catch (error) {
            console.error("Failed to add point to route", error);
        }
    }

    async removePointFromRoute(pointId) {
        if (!this.routeId || !pointId) return;
        try {
            await this.orm.call("wm.route", "action_remove_collection_point", [[this.routeId], pointId]);
            if (this.notification) {
                this.notification.add(_t("Collection point removed from route"), { type: "info" });
            }
            await this.loadRouteData();
        } catch (error) {
            console.error("Failed to remove point from route", error);
        }
    }

    async updateMap(rawValue) {
        if (!this.map) return;

        // Clear existing markers
        this.markers.forEach(marker => marker.remove());
        this.markers = [];

        // Clear polyline
        if (this.polyline) {
            this.polyline.remove();
            this.polyline = null;
        }

        let routePoints = [];
        let otherPoints = [];
        if (rawValue) {
            try {
                const parsed = JSON.parse(rawValue);
                if (Array.isArray(parsed)) {
                    routePoints = parsed;
                } else if (parsed && typeof parsed === "object") {
                    routePoints = parsed.route_points || [];
                    otherPoints = parsed.other_points || [];
                }
            } catch (e) {
                console.error("Failed to parse route_map_data", e);
            }
        }

        this.state.pointCount = routePoints.length;

        const allLatLngs = [];

        // 1. Render all other collection points (not included in route lines)
        otherPoints.forEach((point) => {
            const lat = parseFloat(point.lat);
            const lng = parseFloat(point.lng);
            if (!isNaN(lat) && !isNaN(lng)) {
                const latlng = [lat, lng];
                allLatLngs.push(latlng);

                const icon = L.divIcon({
                    className: 'wm-other-marker-container',
                    html: `
                        <div class="wm-other-marker-pin">
                            <div class="wm-other-marker-circle"><i class="fa fa-map-marker"></i></div>
                            <div class="wm-other-marker-arrow"></div>
                        </div>
                    `,
                    iconSize: [24, 29],
                    iconAnchor: [12, 29],
                    popupAnchor: [0, -31]
                });

                const popupContent = document.createElement("div");
                popupContent.className = "o_map_popup";
                popupContent.innerHTML = `
                    <div class="mb-2">
                        <div class="fw-bold text-muted small"><i class="fa fa-map-marker me-1"></i>Collection Point</div>
                        <div class="fw-bold text-dark" style="font-size: 14px;">${point.name}</div>
                    </div>
                    ${point.address ? `
                    <div class="mb-3">
                        <div class="fw-bold text-muted small">Address</div>
                        <div class="text-break">${point.address}</div>
                    </div>` : ""}
                    <div class="d-flex flex-column gap-2">
                        <button type="button" 
                                class="btn btn-primary btn-sm w-100 d-flex align-items-center justify-content-center gap-1 js_add_to_route" 
                                data-point-id="${point.id}">
                            <i class="fa fa-plus-circle"></i> Add to Route
                        </button>
                        <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                           target="_blank" 
                           class="btn btn-outline-secondary btn-sm w-100 d-flex align-items-center justify-content-center gap-1">
                            <i class="fa fa-location-arrow"></i> Navigate to
                        </a>
                    </div>
                `;

                const marker = L.marker(latlng, { icon })
                    .addTo(this.map)
                    .bindPopup(popupContent);
                this.markers.push(marker);
            }
        });

        // 2. Render route collection points (added in route lines)
        const routeLatLngs = [];
        routePoints.forEach((point) => {
            const lat = parseFloat(point.lat);
            const lng = parseFloat(point.lng);
            if (!isNaN(lat) && !isNaN(lng)) {
                const latlng = [lat, lng];
                routeLatLngs.push(latlng);
                allLatLngs.push(latlng);

                const icon = L.divIcon({
                    className: 'wm-route-marker-container',
                    html: `
                        <div class="wm-route-marker-pin">
                            <div class="wm-route-marker-circle">${point.index}</div>
                            <div class="wm-route-marker-arrow"></div>
                        </div>
                    `,
                    iconSize: [28, 34],
                    iconAnchor: [14, 34],
                    popupAnchor: [0, -36]
                });

                const popupContent = document.createElement("div");
                popupContent.className = "o_map_popup";
                popupContent.innerHTML = `
                    <div class="mb-2">
                        <div class="fw-bold text-muted small">Stop ${point.index}</div>
                        <div class="fw-bold text-primary" style="font-size: 14px;">${point.name}</div>
                    </div>
                    ${point.address ? `
                    <div class="mb-3">
                        <div class="fw-bold text-muted small">Address</div>
                        <div class="text-break">${point.address}</div>
                    </div>` : ""}
                    <div class="d-flex flex-column gap-2">
                        <button type="button" 
                                class="btn btn-outline-danger btn-sm w-100 d-flex align-items-center justify-content-center gap-1 js_remove_from_route" 
                                data-point-id="${point.id}">
                            <i class="fa fa-trash"></i> Remove from Route
                        </button>
                        <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                           target="_blank" 
                           class="btn btn-secondary btn-sm w-100 d-flex align-items-center justify-content-center gap-1">
                            <i class="fa fa-location-arrow"></i> Navigate to
                        </a>
                    </div>
                `;

                const marker = L.marker(latlng, { icon })
                    .addTo(this.map)
                    .bindPopup(popupContent);
                this.markers.push(marker);
            }
        });

        // 3. Draw route polylines and fetch road routing ONLY for route collection points
        if (routeLatLngs.length > 0) {
            if (routeLatLngs.length >= 2) {
                this.polyline = L.polyline(routeLatLngs, {
                    color: '#71639e',
                    weight: 5,
                    opacity: 0.85,
                    dashArray: '8, 8',
                    lineJoin: 'round'
                }).addTo(this.map);

                await this.fetchRoadRoute(routePoints, routeLatLngs);
            }
        }

        // 4. Fit map bounds to show all markers
        if (allLatLngs.length > 0) {
            this.map.fitBounds(allLatLngs, { padding: [60, 60] });
        }
    }

    async fetchRoadRoute(points, latlngs) {
        if (points.length < 2) return;

        const coordString = points
            .map(p => `${parseFloat(p.lng)},${parseFloat(p.lat)}`)
            .join(';');

        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${coordString}?overview=full&geometries=geojson`;

        try {
            const response = await fetch(osrmUrl);
            if (response.ok) {
                const data = await response.json();
                if (data.routes && data.routes.length > 0) {
                    const route = data.routes[0];
                    const routeCoords = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);

                    if (this.polyline) {
                        this.polyline.remove();
                    }

                    this.polyline = L.polyline(routeCoords, {
                        color: '#71639e',
                        weight: 6,
                        opacity: 0.9,
                        lineCap: 'round',
                        lineJoin: 'round'
                    }).addTo(this.map);

                    this.state.totalDistance = (route.distance / 1000).toFixed(1);
                    this.state.totalDuration = Math.round(route.duration / 60);
                }
            }
        } catch (e) {
            console.warn("OSRM road route fetch failed, using direct line fallback", e);
        }
    }
}

registry.category("actions").add("wm_collection.route_map_client_action", WmRouteMapAction);

export class WmRouteMapField extends Component {
    static template = "wm_collection.WmRouteMapField";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.mapContainer = useRef("mapContainer");
        this.map = null;
        this.markers = [];
        this.polyline = null;
        this.resizeObserver = null;
        this.intersectionObserver = null;
        this.lastLatLngs = [];
        this.lastRawValue = null;

        this.state = useState({
            pointCount: 0,
            totalDistance: null,
            totalDuration: null,
        });

        onMounted(() => {
            this.initMap();
            this.loadAndRenderMap();

            if (this.mapContainer.el) {
                this.resizeObserver = new ResizeObserver(() => {
                    if (this.map) {
                        this.map.invalidateSize();
                    }
                });
                this.resizeObserver.observe(this.mapContainer.el);

                if (typeof IntersectionObserver !== "undefined") {
                    this.intersectionObserver = new IntersectionObserver((entries) => {
                        entries.forEach((entry) => {
                            if (entry.isIntersecting && this.map) {
                                setTimeout(() => {
                                    if (this.map) {
                                        this.map.invalidateSize();
                                        if (this.lastLatLngs && this.lastLatLngs.length > 0) {
                                            this.map.fitBounds(this.lastLatLngs, { padding: [60, 60] });
                                        }
                                    }
                                }, 150);
                            }
                        });
                    }, { threshold: 0.1 });
                    this.intersectionObserver.observe(this.mapContainer.el);
                }
            }
        });

        onWillUpdateProps((nextProps) => {
            const nextVal = nextProps.value || nextProps.record?.data?.route_map_data;
            if (nextVal !== this.lastRawValue) {
                this.loadAndRenderMap(nextVal);
            }
        });

        onWillUnmount(() => {
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
            }
            if (this.intersectionObserver) {
                this.intersectionObserver.disconnect();
            }
            if (this.map) {
                this.map.remove();
                this.map = null;
            }
        });
    }

    async loadAndRenderMap(val) {
        let rawData = val !== undefined ? val : (this.props.value || this.props.record?.data?.route_map_data);

        if (!rawData && this.routeId) {
            try {
                const res = await this.orm.read("wm.route", [this.routeId], ["route_map_data"]);
                if (res && res[0] && res[0].route_map_data) {
                    rawData = res[0].route_map_data;
                }
            } catch (e) {
                console.error("Failed to read route_map_data via ORM", e);
            }
        }

        this.lastRawValue = rawData;
        await this.updateMap(rawData);
    }

    initMap() {
        if (!this.mapContainer.el) return;

        this.map = L.map(this.mapContainer.el).setView([0, 0], 2);

        L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        }).addTo(this.map);

        this.map.on('popupopen', (e) => {
            const popupNode = e.popup.getElement();
            if (!popupNode) return;

            const addBtn = popupNode.querySelector('.js_add_to_route');
            if (addBtn) {
                addBtn.addEventListener('click', async (ev) => {
                    ev.preventDefault();
                    const pointId = parseInt(addBtn.dataset.pointId);
                    if (pointId) {
                        this.map.closePopup();
                        await this.addPointToRoute(pointId);
                    }
                });
            }

            const removeBtn = popupNode.querySelector('.js_remove_from_route');
            if (removeBtn) {
                removeBtn.addEventListener('click', async (ev) => {
                    ev.preventDefault();
                    const pointId = parseInt(removeBtn.dataset.pointId);
                    if (pointId) {
                        this.map.closePopup();
                        await this.removePointFromRoute(pointId);
                    }
                });
            }
        });
    }

    get routeId() {
        return this.props.record?.resId || null;
    }

    async addPointToRoute(pointId) {
        if (!this.routeId || !pointId) return;
        try {
            await this.orm.call("wm.route", "action_add_collection_point", [[this.routeId], pointId]);
            if (this.notification) {
                this.notification.add(_t("Collection point added to route & Collection Order created!"), { type: "success" });
            }
            if (this.props.record) {
                await this.props.record.load();
            }
        } catch (error) {
            console.error("Failed to add point to route", error);
        }
    }

    async removePointFromRoute(pointId) {
        if (!this.routeId || !pointId) return;
        try {
            await this.orm.call("wm.route", "action_remove_collection_point", [[this.routeId], pointId]);
            if (this.notification) {
                this.notification.add(_t("Collection point removed from route"), { type: "info" });
            }
            if (this.props.record) {
                await this.props.record.load();
            }
        } catch (error) {
            console.error("Failed to remove point from route", error);
        }
    }

    async updateMap(rawValue) {
        if (!this.map) return;

        this.markers.forEach(marker => marker.remove());
        this.markers = [];

        if (this.polyline) {
            this.polyline.remove();
            this.polyline = null;
        }

        let routePoints = [];
        let otherPoints = [];
        if (rawValue) {
            try {
                const parsed = JSON.parse(rawValue);
                if (Array.isArray(parsed)) {
                    routePoints = parsed;
                } else if (parsed && typeof parsed === "object") {
                    routePoints = parsed.route_points || [];
                    otherPoints = parsed.other_points || [];
                }
            } catch (e) {
                console.error("Failed to parse route_map_data", e);
            }
        }

        this.state.pointCount = routePoints.length;
        const allLatLngs = [];

        otherPoints.forEach((point) => {
            const lat = parseFloat(point.lat);
            const lng = parseFloat(point.lng);
            if (!isNaN(lat) && !isNaN(lng)) {
                const latlng = [lat, lng];
                allLatLngs.push(latlng);

                const icon = L.divIcon({
                    className: 'wm-other-marker-container',
                    html: `
                        <div class="wm-other-marker-pin">
                            <div class="wm-other-marker-circle"><i class="fa fa-map-marker"></i></div>
                            <div class="wm-other-marker-arrow"></div>
                        </div>
                    `,
                    iconSize: [24, 29],
                    iconAnchor: [12, 29],
                    popupAnchor: [0, -31]
                });

                const popupContent = document.createElement("div");
                popupContent.className = "o_map_popup";
                popupContent.innerHTML = `
                    <div class="mb-2">
                        <div class="fw-bold text-muted small"><i class="fa fa-map-marker me-1"></i>Collection Point</div>
                        <div class="fw-bold text-dark" style="font-size: 14px;">${point.name}</div>
                    </div>
                    ${point.address ? `
                    <div class="mb-3">
                        <div class="fw-bold text-muted small">Address</div>
                        <div class="text-break">${point.address}</div>
                    </div>` : ""}
                    <div class="d-flex flex-column gap-2">
                        <button type="button" 
                                class="btn btn-primary btn-sm w-100 d-flex align-items-center justify-content-center gap-1 js_add_to_route" 
                                data-point-id="${point.id}">
                            <i class="fa fa-plus-circle"></i> Add to Route
                        </button>
                        <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                           target="_blank" 
                           class="btn btn-outline-secondary btn-sm w-100 d-flex align-items-center justify-content-center gap-1">
                            <i class="fa fa-location-arrow"></i> Navigate to
                        </a>
                    </div>
                `;

                const marker = L.marker(latlng, { icon })
                    .addTo(this.map)
                    .bindPopup(popupContent);
                this.markers.push(marker);
            }
        });

        const routeLatLngs = [];
        routePoints.forEach((point) => {
            const lat = parseFloat(point.lat);
            const lng = parseFloat(point.lng);
            if (!isNaN(lat) && !isNaN(lng)) {
                const latlng = [lat, lng];
                routeLatLngs.push(latlng);
                allLatLngs.push(latlng);

                const icon = L.divIcon({
                    className: 'wm-route-marker-container',
                    html: `
                        <div class="wm-route-marker-pin">
                            <div class="wm-route-marker-circle">${point.index}</div>
                            <div class="wm-route-marker-arrow"></div>
                        </div>
                    `,
                    iconSize: [28, 34],
                    iconAnchor: [14, 34],
                    popupAnchor: [0, -36]
                });

                const popupContent = document.createElement("div");
                popupContent.className = "o_map_popup";
                popupContent.innerHTML = `
                    <div class="mb-2">
                        <div class="fw-bold text-muted small">Stop ${point.index}</div>
                        <div class="fw-bold text-primary" style="font-size: 14px;">${point.name}</div>
                    </div>
                    ${point.address ? `
                    <div class="mb-3">
                        <div class="fw-bold text-muted small">Address</div>
                        <div class="text-break">${point.address}</div>
                    </div>` : ""}
                    <div class="d-flex flex-column gap-2">
                        <button type="button" 
                                class="btn btn-outline-danger btn-sm w-100 d-flex align-items-center justify-content-center gap-1 js_remove_from_route" 
                                data-point-id="${point.id}">
                            <i class="fa fa-trash"></i> Remove from Route
                        </button>
                        <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                           target="_blank" 
                           class="btn btn-secondary btn-sm w-100 d-flex align-items-center justify-content-center gap-1">
                            <i class="fa fa-location-arrow"></i> Navigate to
                        </a>
                    </div>
                `;

                const marker = L.marker(latlng, { icon })
                    .addTo(this.map)
                    .bindPopup(popupContent);
                this.markers.push(marker);
            }
        });

        if (routeLatLngs.length > 0) {
            if (routeLatLngs.length >= 2) {
                this.polyline = L.polyline(routeLatLngs, {
                    color: '#71639e',
                    weight: 5,
                    opacity: 0.85,
                    dashArray: '8, 8',
                    lineJoin: 'round'
                }).addTo(this.map);

                await this.fetchRoadRoute(routePoints, routeLatLngs);
            }
        }

        this.lastLatLngs = allLatLngs;
        if (allLatLngs.length > 0) {
            this.map.fitBounds(allLatLngs, { padding: [60, 60] });
        }

        setTimeout(() => {
            if (this.map) {
                this.map.invalidateSize();
            }
        }, 200);
    }

    async fetchRoadRoute(points, latlngs) {
        if (points.length < 2) return;

        const coordString = points
            .map(p => `${parseFloat(p.lng)},${parseFloat(p.lat)}`)
            .join(';');

        const osrmUrl = `https://router.project-osrm.org/route/v1/driving/${coordString}?overview=full&geometries=geojson`;

        try {
            const response = await fetch(osrmUrl);
            if (response.ok) {
                const data = await response.json();
                if (data.routes && data.routes.length > 0) {
                    const route = data.routes[0];
                    const routeCoords = route.geometry.coordinates.map(coord => [coord[1], coord[0]]);

                    if (this.polyline) {
                        this.polyline.remove();
                    }

                    this.polyline = L.polyline(routeCoords, {
                        color: '#71639e',
                        weight: 6,
                        opacity: 0.9,
                        lineCap: 'round',
                        lineJoin: 'round'
                    }).addTo(this.map);

                    this.state.totalDistance = (route.distance / 1000).toFixed(1);
                    this.state.totalDuration = Math.round(route.duration / 60);
                }
            }
        } catch (e) {
            console.warn("OSRM road route fetch failed, using direct line fallback", e);
        }
    }
}

export const wmRouteMapField = {
    component: WmRouteMapField,
    supportedTypes: ["text", "html", "char"],
};

registry.category("fields").add("wm_route_map", wmRouteMapField);
