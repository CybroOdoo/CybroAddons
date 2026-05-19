/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Portfolio Grid Widget
 */
publicWidget.registry.PortfolioGrid = publicWidget.Widget.extend({
    selector: ".s_portfolio_grid",
    events: {
        'click .filter-tab': '_onFilterTabClick',
    },

    /**
     * @override
     */
    start: function () {
        this.loadPortfolioData();
        return this._super.apply(this, arguments);
    },

    /**
     * Loads the portfolio data from the server.
     */
    loadPortfolioData: async function () {
        try {
            const data = await rpc('/theme_modern_portfolio/get_portfolio_data');
            this.renderTabs(data.tags);
            this.renderGrid(data.projects);
        } catch (err) {
            console.error("Error loading portfolio data:", err);
        }
    },

    /**
     * Renders the filter tabs.
     */
    renderTabs: function (tags) {
        const tabsContainer = this.el.querySelector("#portfolioTabs");
        if (!tabsContainer) return;

        // Clear existing dynamically added tabs to prevent duplication on save/reload
        const existingTabs = tabsContainer.querySelectorAll("li:not(.tab-all-item)");
        existingTabs.forEach(tab => tab.remove());

        tags.forEach(tag => {
            const li = document.createElement("li");
            li.className = "nav-item dynamic-tab";
            li.setAttribute("role", "presentation");

            const button = document.createElement("button");
            button.className = "nav-link filter-tab";
            button.dataset.filter = tag.id;
            button.setAttribute("type", "button");
            button.setAttribute("role", "tab");
            button.textContent = tag.name;

            li.appendChild(button);
            tabsContainer.appendChild(li);
        });
    },

    /**
     * Renders the portfolio grid cards.
     */
    renderGrid: function (projects) {
        const gridContainer = this.el.querySelector("#portfolioGridContent");
        if (!gridContainer) return;

        gridContainer.innerHTML = ''; // Clear any existing content

        projects.forEach(project => {
            const card = document.createElement("div");
            card.className = "portfolio-card";
            card.dataset.tagIds = JSON.stringify(project.tag_ids || []);

            card.innerHTML = `
                <div class="card-img-wrap">
                    <img src="${project.image_url}" alt="${project.name}"/>
                </div>
                <div class="card-body">
                    <div class="card-text-wrap">
                        <div class="card-title">${project.name}</div>
                        <div class="card-desc">${project.description || ''}</div>
                    </div>
                    <a href="${project.website_url}" class="card-link">
                        <svg viewBox="0 0 24 24">
                            <line x1="7" y1="17" x2="17" y2="7"/>
                            <polyline points="7 7 17 7 17 17"/>
                        </svg>
                    </a>
                </div>
            `;

            gridContainer.appendChild(card);
        });
    },

    /**
     * Handles filter tab clicks using event delegation.
     */
    _onFilterTabClick: function (ev) {
        ev.preventDefault();
        const tab = ev.currentTarget;
        const tabs = this.el.querySelectorAll(".filter-tab");
        const cards = this.el.querySelectorAll(".portfolio-card");

        // Update active state
        tabs.forEach(t => t.classList.remove("active"));
        tab.classList.add("active");

        const filter = tab.dataset.filter;

        // Filter cards
        cards.forEach(card => {
            if (filter === "all") {
                card.style.display = "block";
            } else {
                try {
                    const tagIdsStr = card.dataset.tagIds;
                    const tagIds = tagIdsStr ? JSON.parse(tagIdsStr) : [];
                    if (tagIds.includes(parseInt(filter, 10))) {
                        card.style.display = "block";
                    } else {
                        card.style.display = "none";
                    }
                } catch (err) {
                    console.error("Error parsing tag IDs", err);
                    card.style.display = "none";
                }
            }
        });
    },
});
