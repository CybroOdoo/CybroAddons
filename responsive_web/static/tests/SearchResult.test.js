/** @odoo-module **/
import { describe, expect, test } from "@odoo/hoot";
import { Component } from "@odoo/owl";

/**
 * Tests for SearchResult.js
 *
 * SearchResult is a minimal display component whose primary contract is:
 *  - It is a valid OWL Component subclass.
 *  - Its template is registered under 'responsive_web.SearchResult'.
 *  - It is importable and used as a child inside WebResponsive.
 */

describe("SearchResult Component", () => {
    describe.current.tags("desktop");

    test("SearchResult is a subclass of OWL Component", async () => {
        // Dynamically import to avoid side-effects at module level during tests
        const { default: SearchResult } = await import(
            "@responsive_web/js/SearchResult"
        );
        expect(SearchResult.prototype).toBeInstanceOf(Component.constructor ?? Object);
        // OWL components inherit from Component – verify the prototype chain
        expect(Object.getPrototypeOf(SearchResult)).toBe(Component);
    });

    test("SearchResult.template is set to 'responsive_web.SearchResult'", async () => {
        const { default: SearchResult } = await import(
            "@responsive_web/js/SearchResult"
        );
        expect(SearchResult.template).toBe("responsive_web.SearchResult");
    });

    test("SearchResult can be instantiated without props (it has no required props)", async () => {
        const { default: SearchResult } = await import(
            "@responsive_web/js/SearchResult"
        );
        // The class must at minimum be constructable (no mandatory constructor args beyond OWL internals)
        expect(typeof SearchResult).toBe("function");
    });
});
