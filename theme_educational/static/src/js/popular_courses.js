/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.PopularCourses = publicWidget.Widget.extend({
    selector: "#popular_courses_section",
    events: {
        "click .course-tab": "_onClickTab",
    },

    async _onClickTab(ev) {
        ev.preventDefault();

        const $tab = $(ev.currentTarget);
        const tagId = $tab.data("tag") || false;

        // Switch active tab
        this.$(".course-tab").removeClass("active");
        $tab.addClass("active");

        // AJAX fetch (native)
        const response = await fetch("/popular_courses/filter", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ jsonrpc: "2.0", method: "call", params: { tag_id: tagId }, id: Date.now() }),
        });

        const data = await response.json();

        if (data && data.result) {
            this.$("#course_list").html(data.result);
        }
    },
});
