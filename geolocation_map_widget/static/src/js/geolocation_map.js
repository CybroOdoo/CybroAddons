/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { loadJS, loadCSS } from "@web/core/assets";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { onMounted, onWillUnmount, useEffect, proxy, signal } from "@odoo/owl";

/**
 * Helper to safely extract DOM element from signal.ref() or standard ref object in Odoo 20.
 */
function getRefEl(ref) {
    if (!ref) return null;
    if (typeof ref === "function") return ref();
    return ref.el || null;
}

/**
 * GeoLocationMap class extends CharField to provide an interactive Leaflet map with geolocation features.
 */
export class GeoLocationMap extends CharField {
    static template = "geolocation_map_widget.GeoLocation";

    mapContainerRef = signal.ref();

    setup() {
        super.setup();
        this.state = proxy({
            latitude: 51.505,
            longitude: -0.09,
        });
        this.mapInitialized = false;
        this.leafletMap = null;
        this.currentMarker = null;
        this.lastAddress = (this.props.record && this.props.record.data[this.props.name]) || "";

        let resizeObserver = null;

        onMounted(() => {
            const el = getRefEl(this.mapContainerRef);
            if (el) {
                this._initializeMap();
                if (typeof ResizeObserver !== "undefined") {
                    resizeObserver = new ResizeObserver((entries) => {
                        for (const entry of entries) {
                            if (entry.contentRect.width > 0 && entry.contentRect.height > 0) {
                                if (!this.mapInitialized) {
                                    this._initializeMap();
                                } else if (this.leafletMap) {
                                    this.leafletMap.invalidateSize();
                                }
                            }
                        }
                    });
                    resizeObserver.observe(el);
                }
            }
        });

        onWillUnmount(() => {
            if (resizeObserver) {
                resizeObserver.disconnect();
                resizeObserver = null;
            }
            if (this.leafletMap) {
                this.leafletMap.remove();
                this.leafletMap = null;
            }
            this.currentMarker = null;
            this.mapInitialized = false;
        });

        useEffect(
            () => {
                const currentAddress =
                    (this.props.record && this.props.record.data[this.props.name]) || "";
                if (
                    this.mapInitialized &&
                    currentAddress &&
                    currentAddress !== this.lastAddress
                ) {
                    this.lastAddress = currentAddress;
                    this.getLatLngFromAddress(currentAddress).then(() => {
                        this._updateMapAndMarker();
                    });
                }
            },
            () => [this.props.record && this.props.record.data[this.props.name]]
        );
    }

    /**
     * Loads Leaflet library from local module assets and initializes the interactive map.
     */
    async _initializeMap() {
        const mapContainer = getRefEl(this.mapContainerRef);
        if (!mapContainer || this.mapInitialized) {
            return;
        }
        this.mapInitialized = true;

        if (typeof window.L === "undefined") {
            try {
                await Promise.all([
                    loadJS("/geolocation_map_widget/static/lib/leaflet/leaflet.js"),
                    loadCSS("/geolocation_map_widget/static/lib/leaflet/leaflet.css"),
                ]);
            } catch (err) {
                console.error("[GeoLocationMap] Error loading Leaflet libraries:", err);
                this.mapInitialized = false;
                return;
            }
        }

        if (typeof L === "undefined") {
            console.error("[GeoLocationMap] Leaflet global variable 'L' is undefined!");
            this.mapInitialized = false;
            return;
        }

        if (L.Icon && L.Icon.Default) {
            L.Icon.Default.imagePath = "/geolocation_map_widget/static/lib/leaflet/images/";
        }

        const currentContainer = getRefEl(this.mapContainerRef);
        if (!currentContainer || currentContainer._leaflet_id) {
            return;
        }

        const value =
            (this.props.record && this.props.record.data[this.props.name]) || "";
        if (value) {
            await this.getLatLngFromAddress(value);
        }

        const containerAfterAsync = getRefEl(this.mapContainerRef);
        if (!containerAfterAsync || containerAfterAsync._leaflet_id) {
            return;
        }

        // Initialize the map
        const map = L.map(containerAfterAsync, {
            zoomControl: true,
            zoom: 13,
            zoomAnimation: false,
            fadeAnimation: true,
            markerZoomAnimation: true,
        }).setView([this.state.latitude, this.state.longitude], 13);

        this.leafletMap = map;

        // Add tile layer
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);

        this.currentMarker = L.marker([this.state.latitude, this.state.longitude])
            .addTo(map)
            .bindPopup(_t("Selected Location"))
            .openPopup();

        // Handle map clicks
        map.on("click", async (event) => {
            if (this.props.readonly) {
                return;
            }
            const { lat, lng } = event.latlng;
            this.state.latitude = lat;
            this.state.longitude = lng;
            try {
                const address = await this.getAddressFromLatLng(lat, lng);
                if (!this.props.readonly) {
                    this.lastAddress = address;
                    await this.props.record.update({ [this.props.name]: address });
                }
            } catch (error) {
                console.error("[GeoLocationMap] Error fetching address:", error);
            }
            if (this.currentMarker) {
                map.removeLayer(this.currentMarker);
            }
            this.currentMarker = L.marker([lat, lng])
                .addTo(map)
                .bindPopup(_t("Selected Location"))
                .openPopup();
        });
    }

    _updateMapAndMarker() {
        if (this.leafletMap && this.state.latitude && this.state.longitude) {
            this.leafletMap.setView([this.state.latitude, this.state.longitude], 13);
            if (this.currentMarker) {
                this.leafletMap.removeLayer(this.currentMarker);
            }
            this.currentMarker = L.marker([this.state.latitude, this.state.longitude])
                .addTo(this.leafletMap)
                .bindPopup(_t("Selected Location"))
                .openPopup();
        }
    }

    async onInputChange(ev) {
        if (this.props.readonly) {
            return;
        }
        const newValue = ev.target.value;
        if (newValue) {
            this.lastAddress = newValue;
            await this.getLatLngFromAddress(newValue);
            await this.props.record.update({ [this.props.name]: newValue });
            this._updateMapAndMarker();
        }
    }

    /**
     * Retrieves the address for given coordinates using Nominatim reverse geocoding API.
     */
    async getAddressFromLatLng(latitude, longitude) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`
            );
            const data = await response.json();
            if (!data || !data.address) {
                return data?.display_name || `${latitude}, ${longitude}`;
            }
            const parts = [
                data.address.road ||
                    data.address.suburb ||
                    data.address.village ||
                    data.address.town ||
                    data.address.city,
                data.address.county,
                data.address.state,
                data.address.country,
            ].filter(Boolean);
            return parts.length > 0
                ? parts.join(", ")
                : data.display_name || `${latitude}, ${longitude}`;
        } catch (error) {
            console.error("[GeoLocationMap] Error fetching address:", error);
            return `${latitude}, ${longitude}`;
        }
    }

    /**
     * Converts an address string into latitude and longitude coordinates.
     */
    async getLatLngFromAddress(address) {
        try {
            const response = await fetch(
                `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`
            );
            const data = await response.json();
            if (data && data.length > 0) {
                this.state.latitude = parseFloat(data[0].lat);
                this.state.longitude = parseFloat(data[0].lon);
            }
            return null;
        } catch (error) {
            console.error("[GeoLocationMap] Error fetching coordinates:", error);
            return null;
        }
    }

    /**
     * Opens Google Maps for the current coordinates in a new browser tab.
     */
    _openMapView() {
        const { longitude, latitude } = this.state;
        if (latitude && longitude) {
            window.open(
                `https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`,
                "_blank"
            );
        }
    }
}

export const geoLocationMap = {
    ...charField,
    component: GeoLocationMap,
    displayName: _t("Geolocation Map Viewer"),
};

registry.category("fields").add("geolocation_map", geoLocationMap);
