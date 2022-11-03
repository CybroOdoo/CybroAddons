/** @odoo-module **/
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import VisualEditor from 'backend_theme_infinito.VisualEditor';
import session from 'web.session';
import AdvancedFeatures from 'backend_theme_infinito.AdvancedFeatures';

class InfinitoSystrayItem extends owl.Component {
    setup() {
        this.render();
        this.action = useService("action");
        this.mode = false;
    }
    _onClickSimpleEditor() {
        var $el = $('body')
        this.mode = 'simple';
        $(this.el).find('#dropdown_infinito_mode').hide();
        this._removeEvents($el);
        this._addEvents($el);
        for (var element of $el.find('.dropdown-menu')){
            $(element).removeClass('.dropdown-menu');
        }
    }
    _onClickAdvancedEditor() {
        this.action.doAction('action_theme_studio');
    }
    _removeEvents(element) {
        element = element[0] || element;
        for (var child of element.children) {
            $(child).off();
            this._removeEvents(child);
        }
    }
    _addEvents(element) {
        element = element[0] || element;
        for (var child of element.children) {
            $(child).on('click', this._onClickStudioMode.bind(this));
            this._addEvents(child);
        }
    }
    _onClickStudioMode(e) {
        e.stopPropagation();
        e.preventDefault();
        var $target = $(e.target);
        this.visual_editor = new VisualEditor($target);
        this.visual_editor.open();
    }
}
InfinitoSystrayItem.template = "backend_theme_infinito.StudioSystray";

export const systrayItem = {
    Component: InfinitoSystrayItem,
    isDisplayed: (env) => env.services.user.isAdmin && env.services.ui.size >= 4
};

class InfinitoSystrayAdv extends owl.Component {
    _onClick(){
        if(this.sidebarAdvanced) this.sidebarAdvanced.destroy();
        this.sidebarAdvanced = new AdvancedFeatures(this, 'user');
    }
}


InfinitoSystrayAdv.template = "backend_theme_infinito.AdvSystray";

export const InfinitoSystrayAdvItem = {
    Component: InfinitoSystrayAdv,
    isDisplayed: (env) => session.userEdit && env.services.ui.size >= 4
};

registry.category("systray")
    .add("InfinitoSystrayItem", systrayItem, { sequence: 1 })
    .add("InfinitoSystrayAdv", InfinitoSystrayAdvItem, { sequence: 1 });