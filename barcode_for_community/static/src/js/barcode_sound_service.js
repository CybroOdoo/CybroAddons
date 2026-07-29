/** @odoo-module **/
import { registry } from "@web/core/registry";
export const BarcodeSound = {
    start() {
        function playDanger() {
            var sounds = new Audio('/barcode_for_community/static/src/sounds/danger.wav');
            sounds.load()
            return sounds
        }

        function playAlert() {
            var sounds = new Audio('/barcode_for_community/static/src/sounds/warning.wav');
            sounds.load()
            return sounds
        }

        function playSuccess() {
            var sounds = new Audio('/barcode_for_community/static/src/sounds/success.wav');
            sounds.load()
            return sounds
        }
        return {
            Alert: playAlert(),
            Danger: playDanger(),
            Success: playSuccess(),
        }
    }
}
registry.category('services').add("barcodeSound", BarcodeSound)