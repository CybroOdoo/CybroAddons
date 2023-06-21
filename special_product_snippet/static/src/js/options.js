odoo.define('special_product_snippet.special_product_snippet_options', function (require) {
 'use strict';
    var core = require('web.core');
    var _t = core._t;
    var globalVariable;
    const options = require('web_editor.snippets.options');
    const ajax = require('web.ajax');
    const Many2oneSpecialWidget = options.userValueWidgetsRegistry['we-many2one'];
    const { Component, useExternalListener, onMounted } = owl;
    const QWeb = core.qweb;

    options.registry.SpecialProduct = options.registry.SelectTemplate.extend({
        /**
         * @constructor
         */
        init() {
            this._super(...arguments);
            this.selectTemplateWidgetName = 'special_product_snippet';
        },
        async selectTemplate(previewMode, widgetValue, params) {
            await this._templatesLoading;
            // Call the controller method with parameters
            const response = await ajax.jsonRpc("/website/snippet/special/render", 'call', {
                'template': widgetValue,
                'params': globalVariable
            });
            if (previewMode === 'reset') {
                if (!this.beforePreviewNodes) {
                    return;
                }
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
                this.beforePreviewNodes = [...this.containerEl.childNodes];
            }
            while (this.containerEl.lastChild) {
                this.containerEl.removeChild(this.containerEl.lastChild);
            }
            const temp =  QWeb.render(widgetValue,response.qcontext);
            this.containerEl.insertAdjacentHTML('beforeend',temp);
            if (!previewMode) {
                this.beforePreviewNodes = null;
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
            const { widget } = ev.data;
            globalVariable=widget._methodsParams.recordData
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
});