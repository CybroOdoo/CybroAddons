/** @odoo-module **/

import { Component, onMounted, onWillUnmount, useRef, useEffect } from "@odoo/owl";

export class MapRenderer extends Component {
    static template = "odoo_web_map.MapRenderer";
    static props = {
        "*": true,
    };
    
    setup() {
        this.mapContainer = useRef("mapContainer");
        this.map = null;
        this.markers = []; // Keep track of markers to clear them

        onMounted(() => {
            this.initMap();
        });

        onWillUnmount(() => {
            if (this.map) {
                this.map.remove();
            }
        });

        // Owl effect to update map when records change
        useEffect(() => {
            this.updateMarkers();
        }, () => [this.props.records]);
    }

    getNestedValue(obj, path) {
        // Handle both direct fields and nested paths (e.g., "partner_id.partner_latitude")
        if (!path) return null;

        // First, check if the path exists as a direct key (for our merged data)
        if (path in obj) {
            return obj[path];
        }

        // Otherwise, try to traverse as nested object
        const keys = path.split('.');
        let value = obj;

        for (const key of keys) {
            if (value && typeof value === 'object' && key in value) {
                value = value[key];
            } else {
                return null;
            }
        }

        return value;
    }

    initMap() {
        if (!this.mapContainer.el) return;

        // Configure default Leaflet icon paths dynamically without modifying third-party library files
        if (window.L && L.Icon && L.Icon.Default) {
            delete L.Icon.Default.prototype._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconUrl: '/odoo_web_map/static/lib/leaflet/images/marker-icon.png',
                iconRetinaUrl: '/odoo_web_map/static/lib/leaflet/images/marker-icon-2x.png',
                shadowUrl: '/odoo_web_map/static/lib/leaflet/images/marker-shadow.png',
            });
        }

        // Define default view (e.g., world view or centered on first record)
        // Default to a central point if no data (e.g. 0,0)
        this.map = L.map(this.mapContainer.el).setView([0, 0], 2);

        // Define multiple tile layers
        const streetLayer = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        });

        const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.esri.com/">Esri</a>'
        });

        const terrainLayer = L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
            maxZoom: 17,
            attribution: '&copy; <a href="https://opentopomap.org">OpenTopoMap</a> contributors'
        });

        const cartoDBLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
        });

        // Add default layer
        streetLayer.addTo(this.map);

        // Create layer control
        const baseMaps = {
            "Street": streetLayer,
            "Satellite": satelliteLayer,
            "Terrain": terrainLayer,
            "Light": cartoDBLayer
        };

        L.control.layers(baseMaps).addTo(this.map);

        this.updateMarkers();
    }

    updateMarkers() {
        if (!this.map) return;

        // Clear existing markers
        this.markers.forEach(marker => marker.remove());
        this.markers = [];

        const bounds = [];

        // Group records by location to handle multiple records at same coordinates
        const locationGroups = new Map();

        this.props.records.forEach(record => {
            // Use field names from metaData (which includes related field paths) or fallback to archInfo
            const latField = this.props.metaData?.latField || this.props.archInfo?.latField || "partner_latitude";
            const lngField = this.props.metaData?.lngField || this.props.archInfo?.lngField || "partner_longitude";

            // Access the field value - handle nested paths for related fields
            const lat = this.getNestedValue(record, latField);
            const lng = this.getNestedValue(record, lngField);

            if (lat && lng) {
                // Create a unique key for this location (rounded to avoid floating point issues)
                const locationKey = `${lat.toFixed(6)},${lng.toFixed(6)}`;

                if (!locationGroups.has(locationKey)) {
                    locationGroups.set(locationKey, {
                        lat,
                        lng,
                        records: []
                    });
                }

                locationGroups.get(locationKey).records.push(record);
            }
        });

        // Create markers for each location group
        locationGroups.forEach((group, locationKey) => {
            const { lat, lng, records } = group;

            if (records.length === 1) {
                // Single record - create normal marker
                const marker = this.createMarker(lat, lng, records[0]);
                this.markers.push(marker);
                bounds.push([lat, lng]);
            } else {
                // Multiple records - create cluster marker
                const marker = this.createClusterMarker(lat, lng, records);
                this.markers.push(marker);
                bounds.push([lat, lng]);
            }
        });

        // Fit bounds if we have markers
        if (bounds.length > 0) {
            this.map.fitBounds(bounds, { padding: [50, 50] });
        }
    }

    createMarker(lat, lng, record) {
        const addressField = this.props.metaData?.addressField || this.props.archInfo?.addressField || "contact_address";
        const address = this.getNestedValue(record, addressField) || "";

        // Create DOM element for popup to handle events
        const popupContent = document.createElement("div");
        popupContent.className = "o_map_popup";

        popupContent.innerHTML = `
            <div class="mb-2">
                <div class="fw-bold text-muted small">Name</div>
                <div>${record.display_name}</div>
            </div>
            ${address ? `
            <div class="mb-3">
                <div class="fw-bold text-muted small">Address</div>
                <div class="text-break">${address}</div>
            </div>` : ""}
            <div class="d-flex gap-2">
                <button class="btn btn-primary btn-sm btn-open-record">
                    Open
                </button>
                <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                   target="_blank" 
                   class="btn btn-secondary btn-sm">
                    Navigate to
                </a>
            </div>
        `;

        // Add click listener for Open button
        const openBtn = popupContent.querySelector(".btn-open-record");
        if (openBtn) {
            openBtn.addEventListener("click", () => {
                if (this.props.openRecord) {
                    this.props.openRecord(record);
                }
            });
        }

        const marker = L.marker([lat, lng])
            .addTo(this.map)
            .bindPopup(popupContent);

        return marker;
    }

    createClusterMarker(lat, lng, records) {
        // Create a custom icon with standard marker and count badge
        const icon = L.divIcon({
            className: 'o_map_marker_with_badge',
            html: `
                <div class="o_marker_container">
                    <i class="fa fa-map-marker o_marker_icon"></i>
                    <span class="o_marker_badge">${records.length}</span>
                </div>
            `,
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34]
        });

        const addressField = this.props.metaData?.addressField || this.props.archInfo?.addressField || "contact_address";

        // Create popup content with list of all records
        const popupContent = document.createElement("div");
        popupContent.className = "o_map_popup o_map_cluster_popup";

        let recordsHtml = records.map(record => {
            const address = this.getNestedValue(record, addressField) || "";
            return `
                <div class="o_map_cluster_record mb-2 pb-2 border-bottom">
                    <div class="fw-bold">${record.display_name}</div>
                    ${address ? `<div class="small text-muted text-truncate" style="max-width: 300px;">${address}</div>` : ""}
                    <button class="btn btn-primary btn-sm mt-1 btn-open-record" data-record-id="${record.id}">
                        Open
                    </button>
                </div>
            `;
        }).join('');

        popupContent.innerHTML = `
            <div class="mb-2">
                <div class="fw-bold">${records.length} records at this location</div>
            </div>
            <div class="o_map_cluster_records" style="max-height: 300px; overflow-y: auto;">
                ${recordsHtml}
            </div>
            <div class="mt-2 pt-2 border-top">
                <a href="https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}" 
                   target="_blank" 
                   class="btn btn-secondary btn-sm">
                    Navigate to location
                </a>
            </div>
        `;

        // Add click listeners for all Open buttons
        popupContent.querySelectorAll(".btn-open-record").forEach(btn => {
            btn.addEventListener("click", (e) => {
                const recordId = parseInt(e.target.dataset.recordId);
                const record = records.find(r => r.id === recordId);
                if (record && this.props.openRecord) {
                    this.props.openRecord(record);
                }
            });
        });

        const marker = L.marker([lat, lng], { icon })
            .addTo(this.map)
            .bindPopup(popupContent, { maxWidth: 400 });

        return marker;
    }
}
