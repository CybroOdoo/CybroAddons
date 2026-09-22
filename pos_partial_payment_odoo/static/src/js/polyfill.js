(function () {
    // Polyfill for crypto.randomUUID to support non-secure contexts (HTTP)
    // This is required because Odoo core (e.g., in strings.js) uses crypto.randomUUID(),
    // which is only available in secure contexts (HTTPS or localhost).
    if (typeof crypto !== 'undefined') {
        if (!crypto.randomUUID) {
            crypto.randomUUID = function () {
                return ([1e7] + -1e3 + -4e3 + -8e3 + -1e11).replace(/[018]/g, (c) =>
                    (c ^ (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))).toString(16)
                );
            };
        }
    } else {
        window.crypto = {
            randomUUID: function () {
                return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
                    const r = Math.random() * 16 | 0;
                    const v = c === 'x' ? r : (r & 0x3 | 0x8);
                    return v.toString(16);
                });
            },
            getRandomValues: function (buffer) {
                for (let i = 0; i < buffer.length; i++) {
                    buffer[i] = Math.floor(Math.random() * 256);
                }
                return buffer;
            }
        };
    }
})();
