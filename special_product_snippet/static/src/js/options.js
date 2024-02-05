/** @odoo-module **/
var globalVariable;
import { jsonrpc } from "@web/core/network/rpc_service";
import options from "@web_editor/js/editor/snippets.options";
import { renderToFragment } from "@web/core/utils/render";
const Many2oneSpecialWidget = options.userValueWidgetsRegistry['we-many2one'];
options.registry.SpecialProduct = options.registry.SelectTemplate.extend({
    /**
     * @constructor
     */
    init() {
        this._super(...arguments);
        this.containerSelector = '';
        this.selectTemplateWidgetName = 'special_product_snippet';
        this.orm = this.bindService("orm");
    },
    async selectTemplate(previewMode, widgetValue, params) {
        var self = this;
        if (globalVariable) {
            await this._templatesLoading;
            // Call the controller method with parameters
            const response = await jsonrpc("/website/snippet/special/render", {
                'template': widgetValue,
                'params': globalVariable
            });
            if (previewMode === 'reset') {
                if (!this.beforePreviewNodes) {
                    // FIXME should not be necessary: only needed because we have a
                    // strange 'reset' sent after a non-preview
                    return;
                }
                // Empty the container and restore the original content
                while (this.containerEl.lastChild) {
                    this.containerEl.removeChild(this.containerEl.lastChild);
                }
                for (const node of this.beforePreviewNodes) {
                    this.containerEl.appendChild(node);
                }
                this.beforePreviewNodes = null;
                return;
            }
            if (!this.beforePreviewNodes) {
                // We are about the apply a template on non-previewed content,
                // save that content's nodes.
                this.beforePreviewNodes = [...this.containerEl.childNodes];
            }
            // Empty the container and add the template content
            while (this.containerEl.lastChild) {
                this.containerEl.removeChild(this.containerEl.lastChild);
            }
            const temp = renderToFragment(widgetValue, response.qcontext);
            this.$target.append(temp)
            if (!previewMode) {
                // The original content to keep saved has to be retrieved just
                // before the preview (if we save it now, we might miss other items
                // added by other options or custo).
                this.beforePreviewNodes = null;
            }
        }
    },
});
// getting product from Many2one widget and setting the value in a global
// variable and passing to python and fetching data
const SpecialProductSnippetProduct = Many2oneSpecialWidget.include({
    init(parent, title, options, $target) {
        return this._super(...arguments);
    },
    _onUserValueNotification(ev) {
        const {
            widget
        } = ev.data;
        globalVariable = widget._methodsParams.recordData
        if (widget && widget === this.createInput) {
            ev.stopPropagation();
            return;
        }
        if (widget && widget === this.createButton) {
            if (!this.createInput._value) {
                ev.stopPropagation();
            }
            return;
        }
        if (widget !== this.createButton && this.createInput) {
            this.createInput._value = '';
        }
        return this._super(ev);
    },
});
options.userValueWidgetsRegistry['we-many2one-special'] = Many2oneSpecialWidget;
return {
    SpecialProductSnippetProduct: SpecialProductSnippetProduct,
    SpecialProduct: options.registry.SpecialProduct,
    Many2oneSpecialWidget: Many2oneSpecialWidget,
};
