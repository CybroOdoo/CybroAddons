/** @odoo-module **/
import { tooltipService } from "@web/core/tooltip/tooltip_service";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { Tooltip } from "@web/core/tooltip/tooltip";
import { hasTouch } from "@web/core/browser/feature_detection";
const rpc = require('web.rpc')
import { whenReady } from "@odoo/owl";

const OPEN_DELAY = 400;
const CLOSE_DELAY = 200;
tooltipService.start = (env, { popover }) => {
        let openTooltipTimeout;
        let closeTooltip;
        let target = null;
        let touchPressed;
        const elementsWithTooltips = new Map();

        /**
         * Closes the currently opened tooltip if any, or prevent it from opening.
         */
        function cleanup() {
            browser.clearTimeout(openTooltipTimeout);
            if (closeTooltip) {
                closeTooltip();
            }
        }

        /**
         * Checks that the target is in the DOM and we're hovering the target.
         * @returns {boolean}
         */
        function shouldCleanup() {
            if (!target) {
                return false;
            }
            if (!document.body.contains(target)) {
                return true; // target is no longer in the DOM
            }
            if (hasTouch()) {
                return !touchPressed;
            }
            return false;
        }

        async function getDataFromBackend(info) {
        if (!info?.relation) return
        if (info?.related_record_id){
            const requiredData = await rpc.query({
                model: "product.template",
                method: "read",
                args: [[info.related_record_id], []],
                })
            info.requiredData = requiredData[0];
        }
    }

        /**
         * Checks whether there is a tooltip registered on the event target, and
         * if there is, creates a timeout to open the corresponding tooltip
         * after a delay.
         *
         * @param {HTMLElement} el the element on which to add the tooltip
         * @param {object} param1
         * @param {string} [param1.tooltip] the string to add as a tooltip, if
         *  no tooltip template is specified
         * @param {string} [param1.template] the name of the template to use for
         *  tooltip, if any
         * @param {object} [param1.info] info for the tooltip template
         * @param {'top'|'bottom'|'left'|'right'} param1.position
         * @param {number} [param1.delay] delay after which the popover should
         *  open
         */
        async function openTooltip(el, { tooltip = "", template, info, position, delay = OPEN_DELAY }) {
            await getDataFromBackend(info)
            target = el;
            cleanup();
            if (!tooltip && !template) {
                return;
            }

            openTooltipTimeout = browser.setTimeout(() => {
                // verify that the element is still in the DOM
                if (target.isConnected) {
                    closeTooltip = popover.add(
                        target,
                        Tooltip,
                        { tooltip, template, info },
                        { position }
                    );
                    // Prevent title from showing on a parent at the same time
                    target.title = "";
                }
            }, delay);
        }

        /**
         * Checks whether there is a tooltip registered on the element, and
         * if there is, creates a timeout to open the corresponding tooltip
         * after a delay.
         *
         * @param {HTMLElement} el
         */
        function openElementsTooltip(el) {
            if (elementsWithTooltips.has(el)) {
                openTooltip(el, elementsWithTooltips.get(el));
            } else if (el.matches("[data-tooltip], [data-tooltip-template]")) {
                const dataset = el.dataset;
                const params = {
                    tooltip: dataset.tooltip,
                    template: dataset.tooltipTemplate,
                    position: dataset.tooltipPosition,
                };
                if (dataset.tooltipInfo) {
                    params.info = JSON.parse(dataset.tooltipInfo);
                }
                if (dataset.tooltipDelay) {
                    params.delay = parseInt(dataset.tooltipDelay, 10);
                }
                openTooltip(el, params);
            }
        }

        /**
         * Checks whether there is a tooltip registered on the event target, and
         * if there is, creates a timeout to open the corresponding tooltip
         * after a delay.
         *
         * @param {MouseEvent} ev a "mouseenter" event
         */
        function onMouseenter(ev) {
            openElementsTooltip(ev.target);
        }

        function onMouseleave(ev) {
            if (target === ev.target) {
                cleanup();
            }
        }
        /**
         * Checks whether there is a tooltip registered on the event target, and
         * if there is, creates a timeout to open the corresponding tooltip
         * after a delay.
         *
         * @param {TouchEvent} ev a "touchstart" event
         */
        function onTouchStart(ev) {
            touchPressed = true;
            openElementsTooltip(ev.target);
        }

        whenReady(() => {
            // Regularly check that the target is still in the DOM and if not, close the tooltip
            browser.setInterval(() => {
                if (shouldCleanup()) {
                    cleanup();
                }
            }, CLOSE_DELAY);

            if (hasTouch()) {
                document.body.addEventListener("touchstart", onTouchStart);

                document.body.addEventListener("touchend", (ev) => {
                    if (ev.target.matches("[data-tooltip], [data-tooltip-template]")) {
                        if (!ev.target.dataset.tooltipTouchTapToShow) {
                            touchPressed = false;
                        }
                    }
                });

                document.body.addEventListener("touchcancel", (ev) => {
                    if (ev.target.matches("[data-tooltip], [data-tooltip-template]")) {
                        if (!ev.target.dataset.tooltipTouchTapToShow) {
                            touchPressed = false;
                        }
                    }
                });

                return;
            }

            // Listen (using event delegation) to "mouseenter" events to open the tooltip if any
            document.body.addEventListener("mouseenter", onMouseenter, { capture: true });
            // Listen (using event delegation) to "mouseleave" events to close the tooltip if any
            document.body.addEventListener("mouseleave", onMouseleave, { capture: true });
        });

        return {
            add(el, params) {
                elementsWithTooltips.set(el, params);
                return () => {
                    elementsWithTooltips.delete(el);
                    if (target === el) {
                        cleanup();
                    }
                };
            },
        };
    }
