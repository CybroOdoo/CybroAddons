/** @odoo-module **/
/**
 * This module contains JavaScript code that is used to customize the behavior of the Control Panel
 * in the Odoo web interface. It includes patches to hide filter and groupby options based on
 * the global or custom settings.
 */
import session from 'web.session';
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { useService } from "@web/core/utils/hooks";
import { useState, onMounted, useExternalListener, useRef, useEffect } from "@odoo/owl";
import { patch } from "@web/core/utils/patch";
//This patch is used to hide filter and groupby option on the basis of globally or custom
patch(ControlPanel.prototype, 'hide_filters_groupby.ControlPanel',{
    setup() {
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.pagerProps = this.env.config.pagerProps
            ? useState(this.env.config.pagerProps)
            : undefined;
        this.breadcrumbs = useState(this.env.config.breadcrumbs);
        this.root = useRef("root");
        this.state = useState({
            showSearchBar: false,
            showViewSwitcher: false,
        });
        this.onScrollThrottledBound = this.onScrollThrottled.bind(this);
        useExternalListener(window, "click", this.onWindowClick);
        useEffect(() => {
            if (
                !this.env.isSmall ||
                ("adaptToScroll" in this.display && !this.display.adaptToScroll)
            ) {
                return;
            }
            const scrollingEl = this.getScrollingElement();
            scrollingEl.addEventListener("scroll", this.onScrollThrottledBound);
            this.root.el.style.top = "0px";
            return () => {
                scrollingEl.removeEventListener("scroll", this.onScrollThrottledBound);
            };
        });
        onMounted(() => {
            if (
                !this.env.isSmall ||
                ("adaptToScroll" in this.display && !this.display.adaptToScroll)
            ) {
                return;
            }
            this.oldScrollTop = 0;
            this.lastScrollTop = 0;
            this.initialScrollTop = this.getScrollingElement().scrollTop;
        });
        if (session.is_hide_filters_groupby_enabled == 'True'){
            if (session.hide_filters_groupby == 'global'){
                onMounted(this.hide_globally)
            } else if (session.hide_filters_groupby == 'custom'){
                onMounted(this.hide_on_custom)
            }
        }
    },
    /**
 * Customized method to hide filter and groupby options globally.
 * This method is called when the 'session.hide_filters_groupby_is_enabled' is 'True' and
 * 'session.hide_filters_groupby' is set to 'global'.
 */
    //hides filter and groupby options globally
    hide_globally(){
        this.root.el.querySelector('.o_search_options').style.display = 'none';
    },
    //hides filter and groupby options on custom choice
    /**
 * Customized method to hide filter and groupby options based on custom settings.
 * This method is called when the 'session.hide_filters_groupby_is_enabled' is 'True' and
 * 'session.hide_filters_groupby' is set to 'custom'.
 */
    hide_on_custom(){
    if (this.env.searchModel){
        var model_id = this.env.services.orm.search("ir.model", [["model", "=", this.env.searchModel.resModel]], {
                    limit: 1,
                }).then((value) =>{
                    if (eval(session.ir_model_ids).includes(value[0])){
                        this.root.el.querySelector('.o_search_options').style.display = 'none';
                    }
                });
                }
    }
});
