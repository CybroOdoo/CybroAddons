import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { Component, proxy, t, useProps } from "@odoo/owl";

/**
 * Return the menus a dashboard can be added under: the apps and their sections
 * (menus grouping other menus, without action of their own), as "App / Section".
 *
 * @param {Object} menuService
 * @returns {{ id: number, label: string }[]}
 */
export function getParentMenuOptions(menuService) {
    const options = [];
    const visit = (menu, path) => {
        const label = path ? `${path} / ${menu.name}` : menu.name;
        options.push({ id: menu.id, label });
        for (const childId of menu.children) {
            const child = menuService.getMenu(childId);
            if (child && !child.actionID && child.children.length) {
                visit(child, label);
            }
        }
    };
    for (const app of menuService.getApps()) {
        visit(app, "");
    }
    return options;
}

/**
 * Asked after saving a dashboard in the builder: where should it be in the menus?
 */
export class DashboardMenuDialog extends Component {
    static template = "odoo_dynamic_dashboard.DashboardMenuDialog";
    static components = { Dialog };
    props = useProps({
        close: t.function(),
        menuName: t.string(),
        parentMenuId: t.or([t.number(), t.boolean()]).optional(false),
        isUpdate: t.boolean().optional(false),
        onConfirm: t.function(),
    });

    setup() {
        this.menuService = useService("menu");
        this.parentMenuOptions = getParentMenuOptions(this.menuService);
        this.state = proxy({
            menuName: this.props.menuName,
            parentMenuId: this.props.parentMenuId || false,
            isSaving: false,
        });
    }

    getTitle() {
        return this.props.isUpdate ? _t("Dashboard Menu") : _t("Add the Dashboard to a Menu");
    }

    onNameInput(ev) {
        this.state.menuName = ev.target.value;
    }

    onParentChange(ev) {
        this.state.parentMenuId = parseInt(ev.target.value, 10) || false;
    }

    async confirm() {
        if (!this.state.menuName.trim() || this.state.isSaving) {
            return;
        }
        this.state.isSaving = true;
        try {
            await this.props.onConfirm({
                menuName: this.state.menuName.trim(),
                parentMenuId: this.state.parentMenuId,
            });
        } finally {
            this.state.isSaving = false;
        }
        this.props.close();
    }
}
