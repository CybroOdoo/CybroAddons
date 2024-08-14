/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { CharField, charField } from "@web/views/fields/char/char_field";
import { useRef, useState, onMounted } from "@odoo/owl";
import { registry } from "@web/core/registry";
/**
 * GeoLocationMap class extends CharField to provide a map with geolocation features.
 */
export class GeoLocationMap extends CharField {
    /**
     * Sets up the component by initializing services, references, and state.
     */
    setup() {
        super.setup();
        this.orm = useService('orm');
        this.mapContainerRef = useRef('mapContainer');
        this.state = useState({
            latitude: '51.505',
            longitude: '-0.09',
            address: '',
            currentMarker: null,
        });
        onMounted(() => this._initializeMap());
    }
    /**
     * Initializes the Leaflet map and sets up event handlers.
     * - Configures the map and tile layer.
     * - Adds a click event listener to handle map clicks.
     */
    async _initializeMap() {
        const mapContainer = this.mapContainerRef.el;
        const value = this.input.el.value
        if (value){
            await this.getLatLngFromAddress(value)
        }
        if (!mapContainer) {
            console.error('Map container not found.');
            return;
        }
        // Initialize the map
        const map = L.map(mapContainer,{zoomControl: true,zoom:1,zoomAnimation:false,fadeAnimation:true,markerZoomAnimation:true}).setView([this.state.latitude, this.state.longitude], 13);
        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 15 }).addTo(map);
        this.state.currentMarker = L.marker([this.state.latitude, this.state.longitude])
                .addTo(map)
                .bindPopup('Selected Location')
                .openPopup();
        // Handle map clicks
        map.on('click', async (event) => {
            const { lat, lng } = event.latlng;
            this.state.latitude = lat;
            this.state.longitude = lng;
            try {
                const address = await this.getAddressFromLatLng(lat, lng);
                await this.props.record.update({ [this.props.name]: address });
            } catch (error) {
                console.error('Error fetching address:', error);
            }
            if (this.state.currentMarker) {
                map.removeLayer(this.state.currentMarker);
            }
            const newMarker = L.marker([lat, lng])
                .addTo(map)
                .bindPopup('Selected Location')
                .openPopup();
            this.state.currentMarker = newMarker;
        });
    }
    /**
     * Retrieves the address for the given latitude and longitude using the Nominatim API.
     * @param {number} latitude - Latitude of the location.
     * @param {number} longitude - Longitude of the location.
     * @returns {Promise<string|null>} The formatted address or null if an error occurs.
     */
    async getAddressFromLatLng(latitude, longitude) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/reverse?lat=${latitude}&lon=${longitude}&format=json`);
            const data = await response.json();
            return `${data.address.village || ''}, ${data.address.county || ''}, ${data.address.state || ''}, ${data.address.country || ''}`;
        } catch (error) {
            console.error('Error fetching address:', error);
            return null;
        }
    }
     /**
     * Converts an address into latitude and longitude using Nominatim.
     * @param {string} address - The address to geocode.
     * @returns {Promise<{lat: number, lon: number} | null>} The latitude and longitude, or null if an error occurs.
     */
    async getLatLngFromAddress(address) {
        try {
            const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}`);
            const data = await response.json();
            if (data.length > 0) {
                    this.state.latitude = parseFloat(data[0].lat);
                    this.state.longitude = parseFloat(data[0].lon);
            }
            return null;
        } catch (error) {
            console.error('Error fetching coordinates:', errlatitudeor);
            return null;
        }
    }
    /**
     * Opens a Google Maps view for the current location.
     * The location is determined by the state’s latitude and longitude.
     */
    async _OpenMapview() {
        const { longitude, latitude } = this.state;
        if (latitude && longitude) {
            window.open(`https://www.google.com/maps/search/?api=1&query=${latitude},${longitude}`, '_blank');
        }
    }
}
GeoLocationMap.template = 'GeoLocation';
export const geoLocationMap = {
    ...charField,
    component: GeoLocationMap,
    displayName: _t("GeoLocation Map Viewer"),
};
registry.category("fields").add("geolocation_map", geoLocationMap);
