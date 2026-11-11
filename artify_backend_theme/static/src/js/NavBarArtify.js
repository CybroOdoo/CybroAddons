/*

    Cybrosys Technologies Pvt. Ltd.

    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)

    You can modify it under the terms of the GNU LESSER
    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.

    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
    (LGPL v3) along with this program.
    If not, see <http://www.gnu.org/licenses/>.

*/
import { NavBar } from "@web/webclient/navbar/navbar";
import { patch } from "@web/core/utils/patch";
import { proxy, useEffect } from "@odoo/owl";

const SIDEBAR_OPEN_CLASS = "o_artify_sidebar_open";

patch(NavBar.prototype, {
    setup() {
        super.setup();
        this.sidebar = proxy({ isOpen: false });
        // The layout shift is driven by a body class, see sidebar.scss
        useEffect(() => {
            document.body.classList.toggle(SIDEBAR_OPEN_CLASS, this.sidebar.isOpen);
            return () => document.body.classList.remove(SIDEBAR_OPEN_CLASS);
        });
    },

    /** Toggle the apps sidebar. */
    toggleSidebar() {
        this.sidebar.isOpen = !this.sidebar.isOpen;
    },

    /** Open the selected app and collapse the sidebar. */
    onClickSidebarItem(app) {
        this.onNavBarDropdownItemSelection(app);
        this.sidebar.isOpen = false;
    },
});
