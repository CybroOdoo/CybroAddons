/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Featured Projects Widget
 */
publicWidget.registry.FeaturedProjectsGrid = publicWidget.Widget.extend({
    selector: ".s_portfolio_featured_project",

    /**
     * @override
     */
    start: function () {
        this.loadFeaturedData();
        return this._super.apply(this, arguments);
    },

    /**
     * Loads the featured data from the server.
     */
    loadFeaturedData: async function () {
        try {
            const data = await rpc('/theme_modern_portfolio/get_portfolio_data');
            this.renderGrid(data.projects, data.tags);
        } catch (err) {
            console.error("Error loading featured portfolio data:", err);
        }
    },

    /**
     * Renders the grid content.
     */
    renderGrid: function (projects, tags) {
        const gridContainer = this.el.querySelector("#featuredProjectsGridContent");
        if (!gridContainer) return;

        gridContainer.innerHTML = '';

        // Up to 6 projects for the featured section
        const featuredProjects = projects.slice(0, 6);
        const tagMap = {};
        tags.forEach(t => tagMap[t.id] = t.name);

        const badgeStyles = [
            { colorClass: 'ib-blue', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>' },
            { colorClass: 'ib-purple', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>' },
            { colorClass: 'ib-red', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>' },
            { colorClass: 'ib-green', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="5" width="20" height="14" rx="2"/><line x1="2" y1="10" x2="22" y2="10"/></svg>' },
            { colorClass: 'ib-pink', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>' },
            { colorClass: 'ib-orange', svg: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/></svg>' }
        ];

        featuredProjects.forEach((project, index) => {
            const style = badgeStyles[index % badgeStyles.length];
            const projectTags = (project.tag_ids || []).map(id => tagMap[id]).filter(Boolean);
            const categoryStr = projectTags.length > 0 ? projectTags[0] : 'Featured';

            const tagsHtml = projectTags.slice(0, 3).map(tag => `<span class="tag">${tag}</span>`).join('');

            const cardHtml = `
                <div class="card">
                    <div class="card-top">
                        <div class="card-left">
                            <div class="badge-row">
                                <div class="icon-box ${style.colorClass}">
                                    ${style.svg}
                                </div>
                                <span class="category">${categoryStr}</span>
                            </div>
                            <h3>${project.name}</h3>
                        </div>
                        <a href="${project.website_url}" class="arrow-btn">
                            <svg viewBox="0 0 24 24">
                                <line x1="7" y1="17" x2="17" y2="7"/>
                                <polyline points="7 7 17 7 17 17"/>
                            </svg>
                        </a>
                    </div>
                    <div class="tags">
                        ${tagsHtml}
                    </div>
                    <p>${project.description}</p>
                    <div class="card-img">
                        <img src="${project.image_url}" alt="${project.name}"/>
                    </div>
                </div>
            `;

            gridContainer.insertAdjacentHTML('beforeend', cardHtml);
        });
    },
});
