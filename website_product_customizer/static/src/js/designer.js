/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import { rpc } from "@web/core/network/rpc";
import { WarningDialog } from "@web/core/errors/error_dialogs";

publicWidget.registry.ProductDesigner = publicWidget.Widget.extend({
    selector: '.o_designer_wrap',
    events: {
        // Tool selection
        'click .o_designer_tool': '_onToolClick',

        // Text properties
        'change .o_designer_font_family': '_onFontFamilyChange',
        'input .o_designer_font_size': '_onFontSizeChange',
        'input .o_designer_font_color': '_onFontColorChange',
        'click .o_designer_bold': '_onBoldClick',
        'click .o_designer_italic': '_onItalicClick',
        'click .o_designer_underline': '_onUnderlineClick',
        'click .o_designer_align': '_onAlignClick',
        'input .o_designer_text_curve': '_onTextCurveChange',


        // Variant selector
        'change .o_designer_variant_select': '_onVariantChange',

        // Quantity
        'click .o_designer_qty_minus': '_onQtyMinus',
        'click .o_designer_qty_plus': '_onQtyPlus',
        'change .o_designer_quantity': '_onQtyChange',

        // Actions
        'click .o_designer_add_to_cart': '_onAddToCart',
        'click .o_designer_save': '_onSaveDesign',

        // Zoom
        'click .o_designer_zoom_in': '_onZoomIn',
        'click .o_designer_zoom_out': '_onZoomOut',
        'click .o_designer_fit': '_onZoomFit',

        // Shapes
        'click .o_designer_shape_btn': '_onShapeClick',

        // Background color swatches
        'click .o_designer_bg_swatch': '_onBgSwatchClick',

        // Text color swatches
        'click .o_designer_text_color_swatch': '_onTextColorSwatchClick',

        // Preview
        'click .o_designer_preview': '_onPreviewClick',
        'click .o_designer_preview_side': '_onPreviewSideToggle',

        // Delete
        'click .o_designer_delete': '_onDeleteClick',
        'click .o_designer_clear_all': '_onClearAll',

        // Front/Back
        'click .o_designer_side': '_onSideToggle',

        // Undo/Redo
        'click .o_designer_undo': '_onUndo',
        'click .o_designer_redo': '_onRedo',

        // Admin Edit Area Config
        'click .o_designer_admin_edit_area': '_onToggleEditArea',
        'click .o_designer_admin_save_area': '_onSaveAreaConfig',

        // Admin Save as Template
        'click .o_designer_save_template': '_onSaveAsTemplate',

        // Keyboard mapping for delete
        'keydown': '_onKeydown',
    },

    /**
     * @override
     */
    start() {
        this._super(...arguments);

        // Data and State
        this.canvasElement = this.el.querySelector('#o_designer_canvas_element');
        this.baseImage = this.el.querySelector('.o_designer_base_image');
        const container = this.el.querySelector('.o_designer_canvas');
        this.productId = container?.dataset.productId;
        this.isAdmin = container?.dataset.isAdmin === 'True';
        this.isEditingArea = false;

        // Track the active customization record (for upsert saves)
        const canvasEl = this.el.querySelector('.o_designer_canvas');
        this.customizationId = canvasEl?.dataset.savedCustomizationId
            ? parseInt(canvasEl.dataset.savedCustomizationId) || null
            : null;

        // Track the selected product variant for add-to-cart
        this.variantId = parseInt(canvasEl?.dataset.variantId) || 0;

        // Load limits
        this.maxTexts = parseInt(canvasEl?.dataset.maxTexts) || 0;
        this.maxImages = parseInt(canvasEl?.dataset.maxImages) || 0;
        this.maxChars = parseInt(canvasEl?.dataset.maxCharacters) || 0;

        // Use variant-specific price from data attribute if available, otherwise parse displayed text
        const priceEl = this.el.querySelector('.o_designer_price');
        this.basePrice = parseFloat(priceEl?.dataset.basePrice) ||
            parseFloat(priceEl?.textContent?.replace(/[^\d.,]/g, '') || '0');
        this.quantity = 1;

        // Front/Back State
        const hasFrontBack = canvasEl?.dataset.hasFrontBack === 'True';
        this.currentSide = 'front';
        this.hasFrontBack = hasFrontBack;
        this.designStates = {
            front: null,
            back: null
        };

        // History State per side
        this.history = { front: [], back: [] };
        this.historyIndex = { front: -1, back: -1 };
        this.historyLocked = false;

        // Initialize Fabric Canvas
        if (this.canvasElement) {
            this._initCanvas();
        }

        // Fetch accurate price from server on start (so initial state factors in pricelists)
        this._updatePrice();
    },

    /**
     * Initialize Fabric.js canvas and load initial content
     */
    _initCanvas() {
        // Create fabric canvas
        // We set initial size, but it will be updated when background loads
        this.canvas = new fabric.Canvas('o_designer_canvas_element', {
            selection: true,
            preserveObjectStacking: true,
        });

        // Background Image Handling
        if (this.baseImage) {
            const bgSrc = this.baseImage.src;
            // Hide the original image element as we render it in canvas
            this.baseImage.classList.add('d-none');

            fabric.Image.fromURL(bgSrc, (img) => {
                // Get the natural (original) dimensions of the image
                const naturalWidth = img.width;
                const naturalHeight = img.height;

                // Get container dimensions
                const container = this.el.querySelector('.o_designer_canvas');
                const containerParent = container.parentElement;

                // Calculate available space (use a percentage to leave margin)
                const availableWidth = containerParent.clientWidth * 0.95;
                const availableHeight = containerParent.clientHeight * 0.90;

                // Calculate scale to fit within available space while maintaining aspect ratio
                const scaleX = availableWidth / naturalWidth;
                const scaleY = availableHeight / naturalHeight;
                const scale = Math.min(scaleX, scaleY);

                // Calculate final canvas dimensions
                const canvasWidth = naturalWidth * scale;
                const canvasHeight = naturalHeight * scale;

                // Set canvas dimensions
                this.canvas.setWidth(canvasWidth);
                this.canvas.setHeight(canvasHeight);
                this.baseCanvasWidth = canvasWidth;
                this.baseCanvasHeight = canvasHeight;
                this.currentZoom = 1;

                // Update container to match canvas size for proper centering
                container.style.width = canvasWidth + 'px';
                container.style.height = canvasHeight + 'px';

                // Set background image with proper scaling
                img.set({
                    scaleX: scale,
                    scaleY: scale,
                    originX: 'left',
                    originY: 'top'
                });
                this.canvas.setBackgroundImage(img, this.canvas.renderAll.bind(this.canvas));

                // Store scale factor for relative positioning
                this.canvasScale = scale;
                this.originalWidth = naturalWidth;
                this.originalHeight = naturalHeight;

                // ---- Per-side Design Area Configuration ----
                // Read front design area percentages
                const frontAreaLeft = parseFloat(container.dataset.designAreaLeft || 0);
                const frontAreaTop = parseFloat(container.dataset.designAreaTop || 0);
                const frontAreaWidth = parseFloat(container.dataset.designAreaWidth || 100);
                const frontAreaHeight = parseFloat(container.dataset.designAreaHeight || 100);

                // Read back design area percentages
                const backAreaLeft = parseFloat(container.dataset.designAreaBackLeft || 0);
                const backAreaTop = parseFloat(container.dataset.designAreaBackTop || 0);
                const backAreaWidth = parseFloat(container.dataset.designAreaBackWidth || 100);
                const backAreaHeight = parseFloat(container.dataset.designAreaBackHeight || 100);

                // Helper to create clipPath + visualGuide for a side
                const createDesignAreaObjects = (pctLeft, pctTop, pctWidth, pctHeight) => {
                    const clipLeft = (pctLeft / 100) * canvasWidth;
                    const clipTop = (pctTop / 100) * canvasHeight;
                    const clipWidth = (pctWidth / 100) * canvasWidth;
                    const clipHeight = (pctHeight / 100) * canvasHeight;

                    const clipPath = new fabric.Rect({
                        left: clipLeft,
                        top: clipTop,
                        width: clipWidth,
                        height: clipHeight,
                        absolutePositioned: true
                    });
                    clipPath.canvas = this.canvas;

                    const guide = new fabric.Rect({
                        left: clipLeft,
                        top: clipTop,
                        width: clipWidth,
                        height: clipHeight,
                        fill: 'transparent',
                        stroke: 'rgba(59, 130, 246, 0.5)',
                        strokeWidth: 2,
                        strokeDashArray: [5, 5],
                        selectable: false,
                        evented: false,
                        hasControls: false,
                        excludeFromExport: true,
                        isGuide: true
                    });

                    return { clipPath, guide };
                };

                // Create front side objects
                const frontObjects = createDesignAreaObjects(frontAreaLeft, frontAreaTop, frontAreaWidth, frontAreaHeight);
                // Create back side objects (only meaningful if hasFrontBack)
                const backObjects = createDesignAreaObjects(backAreaLeft, backAreaTop, backAreaWidth, backAreaHeight);

                // Store per-side config
                this.designAreaConfig = {
                    front: {
                        clipPath: frontObjects.clipPath,
                        visualGuide: frontObjects.guide,
                    },
                    back: {
                        clipPath: backObjects.clipPath,
                        visualGuide: backObjects.guide,
                    }
                };

                // Set current (front) as the active design area
                this.designAreaClipPath = this.designAreaConfig.front.clipPath;
                this.visualGuide = this.designAreaConfig.front.visualGuide;
                this.canvas.add(this.visualGuide);

                // Auto-load saved design if one exists
                this._loadSavedDesign();

                // Save initial state
                this._saveState();
            });
        }

        // Bind Events
        this.canvas.on('selection:created', this._onObjectSelected.bind(this));
        this.canvas.on('selection:updated', this._onObjectSelected.bind(this));
        this.canvas.on('selection:cleared', this._onSelectionCleared.bind(this));
        this.canvas.on('object:modified', this._onObjectModified.bind(this));

        // Sync background color with design area live resizing (admin feature initially)
        // Also check bounds for out-of-area highlighting
        this.canvas.on('object:moving', (e) => {
            this._syncBackgroundToGuide(e);
            this._checkObjectBounds(e?.target);
        });
        this.canvas.on('object:scaling', (e) => {
            this._syncBackgroundToGuide(e);
            this._checkObjectBounds(e?.target);
        });

        // Enforce max characters on text input
        this.canvas.on('text:changed', (e) => {
            if (this.maxChars > 0 && e.target.text.length > this.maxChars) {
                // Truncate text and notify user
                e.target.set('text', e.target.text.substring(0, this.maxChars));
                this.canvas.renderAll();
                this.call("dialog", "add", WarningDialog, {
                    title: "Notice",
                    message: `You have reached the maximum character limit of ${this.maxChars} for this text object.`
                });
            }
        });

        this.canvas.on('object:added', (e) => {
            const obj = e.target;
            // Apply absolute clipPath bounding box to the object, ignoring guides/placeholders and selections
            if (obj && !obj.isGuide && !obj.isPlaceholder && !obj.isDesignAreaBg && obj.type !== 'activeSelection' && this.designAreaClipPath) {
                obj.set('clipPath', this.designAreaClipPath);
            }
            this._checkObjectBounds(obj);
            this._saveState();
        });
    },



    // =========================================================================
    // ADMIN CONFIGURATION
    // =========================================================================

    _onToggleEditArea(ev) {
        if (!this.isAdmin || !this.visualGuide) return;

        this.isEditingArea = !this.isEditingArea;
        const editBtn = ev.currentTarget;
        const saveBtn = this.el.querySelector('.o_designer_admin_save_area');

        if (this.isEditingArea) {
            // Enter edit mode
            editBtn.classList.add('active');
            editBtn.innerHTML = '<i class="fa fa-times me-1"></i> Cancel Edit';
            saveBtn.classList.remove('d-none');

            // Make guide selectable and resizable
            this.visualGuide.set({
                selectable: true,
                evented: true,
                hasControls: true,
                stroke: 'rgba(234, 179, 8, 1)', // Highlight yellow
                strokeWidth: 4,
            });
            this.canvas.setActiveObject(this.visualGuide);

            // Temporarily unclip other objects so the admin sees the whole canvas
            this.canvas.getObjects().forEach(obj => {
                if (!obj.isGuide && !obj.isPlaceholder) {
                    obj._oldClipPath = obj.clipPath;
                    obj.set('clipPath', null);
                }
            });
        } else {
            // Exit edit mode (cancel adjustments)
            editBtn.classList.remove('active');
            editBtn.innerHTML = '<i class="fa fa-pencil-square-o me-1"></i> Edit Area';
            saveBtn.classList.add('d-none');

            // Reset guide selection
            this.visualGuide.set({
                selectable: false,
                evented: false,
                hasControls: false,
                stroke: 'rgba(59, 130, 246, 0.5)',
                strokeWidth: 2,
            });
            this.canvas.discardActiveObject();

            // Reapply old clip paths
            this.canvas.getObjects().forEach(obj => {
                if (obj._oldClipPath) {
                    obj.set('clipPath', obj._oldClipPath);
                    delete obj._oldClipPath;
                }
            });
        }

        this.canvas.requestRenderAll();
    },

    async _onSaveAreaConfig(ev) {
        if (!this.isAdmin || !this.visualGuide) return;

        const btn = ev.currentTarget;
        const originalHtml = btn.innerHTML;
        btn.innerHTML = '<i class="fa fa-circle-o-notch fa-spin me-1"></i> Saving...';
        btn.disabled = true;

        // Calculate new percentages
        // Use intrinsic properties and scale to avoid stroke width and zoom offsets from getBoundingRect
        const scaleX = this.visualGuide.scaleX || 1;
        const scaleY = this.visualGuide.scaleY || 1;
        const width = this.visualGuide.width * scaleX;
        const height = this.visualGuide.height * scaleY;
        const left = this.visualGuide.left;
        const top = this.visualGuide.top;

        const leftPct = (left / this.canvas.width) * 100;
        const topPct = (top / this.canvas.height) * 100;
        const widthPct = (width / this.canvas.width) * 100;
        const heightPct = (height / this.canvas.height) * 100;

        try {
            const result = await rpc('/shop/designer/save_area_config', {
                product_id: parseInt(this.productId),
                side: this.currentSide || 'front',
                variant_id: this.variantId || 0,
                config_data: {
                    left: leftPct.toFixed(2),
                    top: topPct.toFixed(2),
                    width: widthPct.toFixed(2),
                    height: heightPct.toFixed(2)
                }
            });

            if (result.success) {
                // Update the current side's clip path bounds
                const currentConfig = this.designAreaConfig[this.currentSide || 'front'];
                this.designAreaClipPath.set({
                    left: left,
                    top: top,
                    width: width,
                    height: height,
                    scaleX: 1,
                    scaleY: 1
                });
                currentConfig.clipPath = this.designAreaClipPath;

                // Also reset visual guide's scale and width/height so stroke isn't distorted next time
                this.visualGuide.set({
                    width: width,
                    height: height,
                    scaleX: 1,
                    scaleY: 1
                });
                currentConfig.visualGuide = this.visualGuide;

                // Update background rect if it exists
                const bgRect = this.canvas.getObjects().find(o => o.isDesignAreaBg);
                if (bgRect) {
                    bgRect.set({
                        left: left,
                        top: top,
                        width: width,
                        height: height,
                        scaleX: 1,
                        scaleY: 1,
                        clipPath: this.designAreaClipPath
                    });
                }

                // Exit edit mode successfully
                this._onToggleEditArea({ currentTarget: this.el.querySelector('.o_designer_admin_edit_area') });
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: "Notice",
                    message: 'Failed to save configuration: ' + (result.error || 'Unknown error')
                });
            }
        } catch (err) {

            this.call("dialog", "add", WarningDialog, {
                title: "Notice",
                message: 'An error occurred while saving.'
            });
        } finally {
            btn.innerHTML = originalHtml;
            btn.disabled = false;
        }
    },

    // =========================================================================
    // EVENT HANDLERS - Canvas & Objects
    // =========================================================================

    _onObjectSelected(e) {
        const obj = e.selected ? e.selected[0] : e.target;
        if (!obj) return;

        // Show shared tools
        const objectPanel = this.el.querySelector('.o_designer_object_panel');
        if (objectPanel) objectPanel.classList.remove('d-none');

        // Show text tools if text
        const textPanel = this.el.querySelector('.o_designer_text_panel');
        if (obj.type === 'i-text' || obj.type === 'text') {
            textPanel.classList.remove('d-none');
            this._syncTextPanel(obj);
        } else {
            textPanel.classList.add('d-none');
        }

        // Check for placeholder interaction
        if (obj.isPlaceholder) {
            // Maybe show upload button
            this._openImageUpload(obj);
        }
    },

    _onSelectionCleared() {
        this.el.querySelector('.o_designer_text_panel').classList.add('d-none');
        const objectPanel = this.el.querySelector('.o_designer_object_panel');
        if (objectPanel) objectPanel.classList.add('d-none');
    },

    /**
     * Keep the background color strictly filling the design area as the admin dynamically resizes it.
     */
    _syncBackgroundToGuide(e) {
        if (!e || !e.target || !e.target.isGuide) return;

        const target = e.target;
        const scaleX = target.scaleX || 1;
        const scaleY = target.scaleY || 1;
        const width = target.width * scaleX;
        const height = target.height * scaleY;
        const left = target.left;
        const top = target.top;

        if (this.designAreaClipPath) {
            this.designAreaClipPath.set({
                left: left,
                top: top,
                width: width,
                height: height,
                scaleX: 1,
                scaleY: 1
            });
        }

        const bgRect = this.canvas.getObjects().find(o => o.isDesignAreaBg);
        if (bgRect) {
            bgRect.set({
                left: left,
                top: top,
                width: width,
                height: height,
                scaleX: 1,
                scaleY: 1,
                clipPath: this.designAreaClipPath
            });
        }
    },

    _onObjectModified(e) {
        if (e && e.target) {
            this._checkObjectBounds(e.target);
        }
        this._saveState();
    },

    /**
     * Check whether the given Fabric object extends beyond the design area.
     * If it does, highlight with red selection borders; otherwise reset to defaults.
     */
    _checkObjectBounds(obj) {
        if (!obj || obj.isGuide || obj.isPlaceholder || obj.isDesignAreaBg || !this.designAreaClipPath) {
            return;
        }
        // Handle active selections (multiple selected objects)
        if (obj.type === 'activeSelection') {
            (obj._objects || []).forEach(o => this._checkObjectBounds(o));
            return;
        }
        const objBounds = obj.getBoundingRect(true, true);
        const area = this.designAreaClipPath;
        const aLeft = area.left;
        const aTop = area.top;
        const aRight = aLeft + area.width * (area.scaleX || 1);
        const aBottom = aTop + area.height * (area.scaleY || 1);

        const isOutside = (
            objBounds.left < aLeft - 1 ||
            objBounds.top < aTop - 1 ||
            objBounds.left + objBounds.width > aRight + 1 ||
            objBounds.top + objBounds.height > aBottom + 1
        );

        if (isOutside) {
            obj.set({
                borderColor: '#ff0000',
                cornerColor: '#ff0000',
                cornerStrokeColor: '#ff0000',
            });
        } else {
            obj.set({
                borderColor: 'rgba(102,153,255,0.75)',
                cornerColor: 'rgba(102,153,255,0.75)',
                cornerStrokeColor: 'rgba(102,153,255,0.75)',
            });
        }
        if (this.canvas) {
            this.canvas.requestRenderAll();
        }
    },

    // =========================================================================
    // SYNC UI
    // =========================================================================

    _syncTextPanel(obj) {
        const styles = {
            fontFamily: obj.fontFamily,
            fontSize: Math.round(obj.fontSize / this.canvasScale), // Show logical size
            fill: obj.fill,
            fontWeight: obj.fontWeight,
            fontStyle: obj.fontStyle,
            underline: obj.underline,
            textAlign: obj.textAlign
        };

        const fontFamily = this.el.querySelector('.o_designer_font_family');
        if (fontFamily) fontFamily.value = styles.fontFamily;

        const fontSize = this.el.querySelector('.o_designer_font_size');
        if (fontSize) fontSize.value = styles.fontSize;
        this.el.querySelector('.o_designer_font_size_label').textContent = styles.fontSize + 'px';

        const fontColor = this.el.querySelector('.o_designer_font_color');
        if (fontColor) fontColor.value = styles.fill;

        this._updateStyleButton('.o_designer_bold', styles.fontWeight === 'bold');
        this._updateStyleButton('.o_designer_italic', styles.fontStyle === 'italic');
        this._updateStyleButton('.o_designer_underline', !!styles.underline);

        this.el.querySelectorAll('.o_designer_align').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.align === styles.textAlign);
        });
    },

    _updateStyleButton(selector, active) {
        const btn = this.el.querySelector(selector);
        if (btn) {
            btn.classList.toggle('active', active);
            btn.classList.toggle('btn-primary', active);
            btn.classList.toggle('btn-outline-secondary', !active);
        }
    },

    // =========================================================================
    // TOOL ACTIONS
    // =========================================================================

    _onToolClick(ev) {
        const btn = ev.currentTarget;
        const tool = btn.dataset.tool;

        // Clear active state from all tools — no tool stays selected
        this.el.querySelectorAll('.o_designer_tool').forEach(t => t.classList.remove('active'));

        // Toggle Panels
        const shapesPanel = this.el.querySelector('.o_designer_shapes_panel');
        if (shapesPanel) {
            if (tool === 'shapes') {
                shapesPanel.classList.remove('d-none');
            } else {
                shapesPanel.classList.add('d-none');
            }
        }

        const bgPanel = this.el.querySelector('.o_designer_bg_panel');
        if (bgPanel) {
            if (tool === 'background') {
                bgPanel.classList.remove('d-none');
            } else {
                bgPanel.classList.add('d-none');
            }
        } else if (tool === 'background') {
            this.call("dialog", "add", WarningDialog, {
                title: "No Background Colors",
                message: "Background colors have not been configured for this product. Please contact the administrator to set up color options."
            });
        }

        const templatesPanel = this.el.querySelector('.o_designer_templates_panel');
        if (templatesPanel) {
            if (tool === 'templates') {
                templatesPanel.classList.remove('d-none');
                this._loadTemplates();
            } else {
                templatesPanel.classList.add('d-none');
            }
        }

        if (tool === 'text') {
            this._addText();
        } else if (tool === 'image') {
            this._openImageUpload();
        }
    },

    /**
     * Fetch available design templates from the server and render them in the panel.
     */
    _loadTemplates() {
        const productId = this.el.querySelector('.o_designer_canvas')?.dataset?.productId;
        const grid = this.el.querySelector('.o_designer_templates_grid');
        if (!grid || !productId) return;

        grid.innerHTML = '<p class="text-muted small w-100 text-center"><i class="fa fa-spinner fa-spin me-1"></i> Loading...</p>';

        rpc('/shop/designer/get_templates', {
            product_id: parseInt(productId),
        }).then((templates) => {
            if (!templates || templates.length === 0) {
                grid.innerHTML = '<p class="text-muted small w-100 text-center">No templates available for this product.</p>';
                return;
            }

            grid.innerHTML = '';
            templates.forEach((tmpl) => {
                const card = document.createElement('div');
                card.className = 'o_designer_template_card border rounded p-1 text-center position-relative';
                card.style.cssText = 'width:100px;cursor:pointer;transition:all 0.2s;';
                card.dataset.templateId = tmpl.id;
                card.dataset.designData = tmpl.design_data || '';

                // Admin edit button
                const editBtnHtml = this.isAdmin
                    ? `<button class="btn btn-sm btn-outline-warning o_designer_template_edit position-absolute"
                               style="top:2px;right:2px;padding:1px 5px;font-size:10px;z-index:2;"
                               title="Edit Template" data-template-id="${tmpl.id}">
                           <i class="fa fa-pencil"></i>
                       </button>`
                    : '';

                card.innerHTML = `
                    ${editBtnHtml}
                    <img src="${tmpl.preview_url}" alt="${tmpl.name}" 
                         style="width:100%;height:70px;object-fit:cover;border-radius:4px;"
                         onerror="this.src='/web/static/img/placeholder.png'"/>
                    <small class="d-block mt-1 text-truncate">${tmpl.name}</small>
                `;

                // Apply template on card click (but not on edit button click)
                card.addEventListener('click', (e) => {
                    if (e.target.closest('.o_designer_template_edit')) return;
                    this._applyTemplate(tmpl);
                });

                // Admin: edit button handler
                if (this.isAdmin) {
                    const editBtn = card.querySelector('.o_designer_template_edit');
                    if (editBtn) {
                        editBtn.addEventListener('click', (e) => {
                            e.stopPropagation();
                            this._editTemplate(tmpl);
                        });
                    }
                }

                card.addEventListener('mouseenter', () => { card.style.borderColor = '#3B82F6'; card.style.transform = 'scale(1.05)'; });
                card.addEventListener('mouseleave', () => { card.style.borderColor = ''; card.style.transform = ''; });
                grid.appendChild(card);
            });
        }).catch(() => {
            grid.innerHTML = '<p class="text-danger small w-100 text-center">Failed to load templates.</p>';
        });
    },

    /**
     * Apply a design template to the current canvas.
     */
    _applyTemplate(tmpl) {
        if (!tmpl.design_data || !this.canvas) return;

        if (!confirm(`Apply template "${tmpl.name}"? This will replace your current design.`)) return;

        try {
            const designObj = typeof tmpl.design_data === 'string' ? JSON.parse(tmpl.design_data) : tmpl.design_data;

            if (this.hasFrontBack && designObj.front !== undefined) {
                this.designStates.front = designObj.front;
                this.designStates.back = designObj.back || null;

                this._loadDesignJSON(this.designStates[this.currentSide], () => {
                    this._saveState();
                });
            } else {
                if (this.currentSide) {
                    this.designStates[this.currentSide] = designObj;
                }
                this._loadDesignJSON(designObj, () => {
                    this._saveState();
                });
            }
        } catch (e) {
            this.call("dialog", "add", WarningDialog, {
                title: "Error",
                message: 'Failed to apply template: ' + e.message
            });
        }
    },

    /**
     * Start editing an existing template (admin only).
     * Loads the template onto the canvas and enters "editing" mode.
     */
    _editTemplate(tmpl) {
        if (!tmpl.design_data || !this.canvas) return;

        if (!confirm(`Edit template "${tmpl.name}"? This will replace your current design.`)) return;

        // Load template onto canvas
        try {
            const designObj = typeof tmpl.design_data === 'string' ? JSON.parse(tmpl.design_data) : tmpl.design_data;

            if (this.hasFrontBack && designObj.front !== undefined) {
                this.designStates.front = designObj.front;
                this.designStates.back = designObj.back || null;
                this._loadDesignJSON(this.designStates[this.currentSide], () => {
                    this._saveState();
                });
            } else {
                if (this.currentSide) {
                    this.designStates[this.currentSide] = designObj;
                }
                this._loadDesignJSON(designObj, () => {
                    this._saveState();
                });
            }
        } catch (e) {
            this.call("dialog", "add", WarningDialog, {
                title: "Error",
                message: 'Failed to load template for editing: ' + e.message
            });
            return;
        }

        // Enter editing mode
        this.editingTemplateId = tmpl.id;
        this.editingTemplateName = tmpl.name;
        this._updateTemplateButton();
    },

    /**
     * Update the "Save as Template" button to reflect editing state.
     */
    _updateTemplateButton() {
        const btn = this.el.querySelector('.o_designer_save_template');
        if (!btn) return;

        if (this.editingTemplateId) {
            btn.innerHTML = '<i class="fa fa-pencil me-1"></i> Update Template';
            btn.title = `Editing: ${this.editingTemplateName}`;
            btn.classList.remove('btn-outline-info');
            btn.classList.add('btn-info');

            // Add cancel button if not already there
            if (!this.el.querySelector('.o_designer_cancel_template_edit')) {
                const cancelBtn = document.createElement('button');
                cancelBtn.className = 'btn btn-sm btn-outline-secondary o_designer_cancel_template_edit';
                cancelBtn.title = 'Cancel Template Editing';
                cancelBtn.innerHTML = '<i class="fa fa-times"></i>';
                cancelBtn.addEventListener('click', () => this._clearTemplateEditing());
                btn.parentNode.insertBefore(cancelBtn, btn.nextSibling);
            }
        } else {
            btn.innerHTML = '<i class="fa fa-bookmark me-1"></i> Save as Template';
            btn.title = 'Save as Template';
            btn.classList.remove('btn-info');
            btn.classList.add('btn-outline-info');

            // Remove cancel button
            const cancelBtn = this.el.querySelector('.o_designer_cancel_template_edit');
            if (cancelBtn) cancelBtn.remove();
        }
    },

    /**
     * Cancel template editing mode and revert button state.
     */
    _clearTemplateEditing() {
        this.editingTemplateId = null;
        this.editingTemplateName = null;
        this._updateTemplateButton();
    },

    _addText() {
        if (this.maxTexts > 0) {
            const currentTexts = this.canvas.getObjects().filter(o => o.type === 'i-text' || o.type === 'text').length;
            if (currentTexts >= this.maxTexts) {
                this.call("dialog", "add", WarningDialog, {
                    title: "Notice",
                    message: `You can only add up to ${this.maxTexts} text elements.`
                });
                return;
            }
        }

        const text = new fabric.IText('New Text', {
            left: this.canvas.width / 2,
            top: this.canvas.height / 2,
            fontFamily: 'Arial',
            fontSize: 24 * this.canvasScale,
            fill: '#000000',
            originX: 'center',
            originY: 'center'
        });

        // Ensure starting text obeys the limit if it is smaller than 'New Text' (8 chars)
        if (this.maxChars > 0 && text.text.length > this.maxChars) {
            text.set('text', text.text.substring(0, this.maxChars));
        }

        this.canvas.add(text);
        this.canvas.setActiveObject(text);
        this.canvas.renderAll();
        this._saveState();
    },

    _onShapeClick(ev) {
        const shapeType = ev.currentTarget.dataset.shape;
        let shape;
        const commonProps = {
            left: this.canvas.width / 2,
            top: this.canvas.height / 2,
            fill: '#808080',
            originX: 'center',
            originY: 'center',
            width: 100 * this.canvasScale,
            height: 100 * this.canvasScale
        };

        if (shapeType === 'rect') {
            shape = new fabric.Rect(commonProps);
        } else if (shapeType === 'circle') {
            // Circle uses radius instead of width/height for size
            shape = new fabric.Circle({
                ...commonProps,
                radius: 50 * this.canvasScale
            });
        } else if (shapeType === 'triangle') {
            shape = new fabric.Triangle(commonProps);
        }

        if (shape) {
            this.canvas.add(shape);
            this.canvas.setActiveObject(shape);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    // =========================================================================
    // PROPERTY UPDATES
    // =========================================================================

    _getActiveTextObj() {
        const obj = this.canvas.getActiveObject();
        return (obj && (obj.type === 'i-text' || obj.type === 'text')) ? obj : null;
    },

    _onFontFamilyChange(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            obj.set('fontFamily', ev.currentTarget.value);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onFontSizeChange(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            const size = parseInt(ev.currentTarget.value);
            obj.set('fontSize', size * this.canvasScale);
            this.el.querySelector('.o_designer_font_size_label').textContent = size + 'px';
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onFontColorChange(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            obj.set('fill', ev.currentTarget.value);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    /**
     * Handle click on a text color swatch (admin-configured colors)
     */
    _onTextColorSwatchClick(ev) {
        const color = ev.currentTarget.dataset.color;
        const obj = this._getActiveTextObj();
        if (obj && color) {
            obj.set('fill', color);
            // Highlight active swatch
            this.el.querySelectorAll('.o_designer_text_color_swatch').forEach(s => {
                s.style.borderColor = s.dataset.color === color ? '#0d6efd' : '#dee2e6';
            });
            this.canvas.renderAll();
            this._saveState();
        }
    },

    /**
     * Handle click on a background color swatch
     */
    _onBgSwatchClick(ev) {
        const color = ev.currentTarget.dataset.color;
        if (!this.canvas || !color || !this.visualGuide) return;

        let bgRect = this.canvas.getObjects().find(o => o.isDesignAreaBg);

        if (color === 'transparent') {
            if (bgRect) {
                this.canvas.remove(bgRect);
            }
        } else {
            if (!bgRect) {
                bgRect = new fabric.Rect({
                    left: this.visualGuide.left,
                    top: this.visualGuide.top,
                    width: this.visualGuide.width * (this.visualGuide.scaleX || 1),
                    height: this.visualGuide.height * (this.visualGuide.scaleY || 1),
                    fill: color,
                    selectable: false,
                    evented: false,
                    hasControls: false,
                    isDesignAreaBg: true,
                    clipPath: this.designAreaClipPath // Optional, but keeps consistency
                });
                this.canvas.add(bgRect);
                bgRect.sendToBack();
            } else {
                bgRect.set('fill', color);
            }
        }

        // Highlight active swatch
        this.el.querySelectorAll('.o_designer_bg_swatch').forEach(s => {
            s.style.borderColor = s.dataset.color === color ? '#0d6efd' : '#dee2e6';
        });

        // Ensure canvas background is cleared in case it was set previously
        this.canvas.setBackgroundColor('', this.canvas.renderAll.bind(this.canvas));
        this._saveState();
    },

    _onBoldClick(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            const isBold = obj.fontWeight === 'bold';
            obj.set('fontWeight', isBold ? 'normal' : 'bold');
            this._updateStyleButton('.o_designer_bold', !isBold);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onItalicClick(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            const isItalic = obj.fontStyle === 'italic';
            obj.set('fontStyle', isItalic ? 'normal' : 'italic');
            this._updateStyleButton('.o_designer_italic', !isItalic);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onUnderlineClick(ev) {
        const obj = this._getActiveTextObj();
        if (obj) {
            obj.set('underline', !obj.underline);
            this._updateStyleButton('.o_designer_underline', !obj.underline); // Note: !obj.underline because we just toggled it? No wait, obj.underline is now new value
            this._updateStyleButton('.o_designer_underline', obj.underline);
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onAlignClick(ev) {
        const obj = this._getActiveTextObj();
        const align = ev.currentTarget.dataset.align;
        if (obj) {
            obj.set('textAlign', align);
            this.el.querySelectorAll('.o_designer_align').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.align === align);
            });
            this.canvas.renderAll();
            this._saveState();
        }
    },

    _onTextCurveChange(ev) {
        const angle = parseInt(ev.target.value); // -180 to 180
        this.el.querySelector('.o_designer_text_curve_label').textContent = angle + '°';

        const activeObj = this.canvas.getActiveObject();
        if (!activeObj) return;

        if (activeObj.type === 'i-text' || activeObj.type === 'text') {
            // Text Curve Logic
            if (angle === 0) {
                activeObj.set({ path: null });
            } else {
                const pathStr = `M 0 0 Q ${activeObj.width / 2} ${angle * -2} ${activeObj.width} 0`;
                const path = new fabric.Path(pathStr, {
                    fill: '',
                    stroke: '',
                    objectCaching: false
                });

                activeObj.set({
                    path: path,
                    pathSide: angle > 0 ? 'right' : 'left',
                    pathAlign: 'center'
                });
            }
        } else if (activeObj.type === 'image') {
            // Image Cylindrical Warping
            if (angle === 0) {
                // Reset to original image
                if (activeObj._originalImageElement) {
                    const resetImg = new fabric.Image(activeObj._originalImageElement, {
                        left: activeObj.left,
                        top: activeObj.top,
                        scaleX: activeObj.scaleX,
                        scaleY: activeObj.scaleY,
                        angle: activeObj.angle,
                        originX: activeObj.originX,
                        originY: activeObj.originY
                    });
                    this.canvas.remove(activeObj);
                    this.canvas.add(resetImg);
                    this.canvas.setActiveObject(resetImg);
                }
            } else {
                // Apply cylindrical warp
                this._applyCylindricalWarp(activeObj, angle / 180);
            }
        }

        this.canvas.requestRenderAll();
    },

    _applyCylindricalWarp(imageObj, intensity) {
        // Store original image element if not already stored
        if (!imageObj._originalImageElement) {
            imageObj._originalImageElement = imageObj.getElement();
        }

        const originalImg = imageObj._originalImageElement;
        const width = originalImg.width || originalImg.naturalWidth;
        const height = originalImg.height || originalImg.naturalHeight;

        // Create offscreen canvases
        const srcCanvas = document.createElement('canvas');
        srcCanvas.width = width;
        srcCanvas.height = height;
        const srcCtx = srcCanvas.getContext('2d');
        srcCtx.drawImage(originalImg, 0, 0, width, height);

        const dstCanvas = document.createElement('canvas');
        dstCanvas.width = width;
        dstCanvas.height = height;
        const dstCtx = dstCanvas.getContext('2d');

        // Get source image data
        const srcImageData = srcCtx.getImageData(0, 0, width, height);
        const dstImageData = dstCtx.createImageData(width, height);

        // Clear destination with transparency
        for (let i = 0; i < dstImageData.data.length; i += 4) {
            dstImageData.data[i + 3] = 0; // Transparent
        }

        // Apply barrel/bulge distortion for cylindrical wrapping
        const centerX = width / 2;
        const centerY = height / 2;
        const maxRadius = Math.sqrt(centerX * centerX + centerY * centerY);

        // Intensity controls the strength of the bulge effect
        const bulgeStrength = intensity * 0.5; // Scale down for smoother effect

        for (let y = 0; y < height; y++) {
            for (let x = 0; x < width; x++) {
                // Calculate distance from center
                const dx = x - centerX;
                const dy = y - centerY;
                const distance = Math.sqrt(dx * dx + dy * dy);
                const normalizedDistance = distance / maxRadius;

                // Apply barrel distortion
                // Positive intensity = bulge outward (barrel)
                // The distortion is stronger at the edges
                const distortionFactor = 1 + bulgeStrength * normalizedDistance * normalizedDistance;

                // Calculate source coordinates
                const srcX = centerX + dx / distortionFactor;
                const srcY = centerY + dy / distortionFactor;

                // Bilinear interpolation for smooth results
                if (srcX >= 0 && srcX < width - 1 && srcY >= 0 && srcY < height - 1) {
                    const x0 = Math.floor(srcX);
                    const x1 = x0 + 1;
                    const y0 = Math.floor(srcY);
                    const y1 = y0 + 1;

                    const fx = srcX - x0;
                    const fy = srcY - y0;

                    const dstIdx = (y * width + x) * 4;

                    // Get four neighboring pixels
                    const idx00 = (y0 * width + x0) * 4;
                    const idx10 = (y0 * width + x1) * 4;
                    const idx01 = (y1 * width + x0) * 4;
                    const idx11 = (y1 * width + x1) * 4;

                    // Interpolate each channel
                    for (let c = 0; c < 4; c++) {
                        const v00 = srcImageData.data[idx00 + c];
                        const v10 = srcImageData.data[idx10 + c];
                        const v01 = srcImageData.data[idx01 + c];
                        const v11 = srcImageData.data[idx11 + c];

                        const v0 = v00 * (1 - fx) + v10 * fx;
                        const v1 = v01 * (1 - fx) + v11 * fx;
                        const v = v0 * (1 - fy) + v1 * fy;

                        dstImageData.data[dstIdx + c] = Math.round(v);
                    }
                }
            }
        }

        dstCtx.putImageData(dstImageData, 0, 0);

        // Create new Fabric image from warped canvas
        fabric.Image.fromURL(dstCanvas.toDataURL(), (warpedImg) => {
            warpedImg.set({
                left: imageObj.left,
                top: imageObj.top,
                scaleX: imageObj.scaleX,
                scaleY: imageObj.scaleY,
                angle: imageObj.angle,
                originX: imageObj.originX,
                originY: imageObj.originY,
                _originalImageElement: imageObj._originalImageElement
            });

            this.canvas.remove(imageObj);
            this.canvas.add(warpedImg);
            this.canvas.setActiveObject(warpedImg);
            this.canvas.requestRenderAll();
        });
    },

    // =========================================================================
    // IMAGE UPLOAD
    // =========================================================================

    _openImageUpload(placeholderObj = null) {
        if (!placeholderObj && this.maxImages > 0) {
            const currentImages = this.canvas.getObjects().filter(o => o.type === 'image' && !o.isDesignAreaBg && o !== this.canvas.backgroundImage).length;
            if (currentImages >= this.maxImages) {
                this.call("dialog", "add", WarningDialog, {
                    title: "Notice",
                    message: `You can only add up to ${this.maxImages} image elements.`
                });
                return;
            }
        }

        const input = document.createElement('input');
        input.type = 'file';
        input.accept = 'image/png, image/jpeg, image/jpg, image/svg+xml';
        input.onchange = async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const reader = new FileReader();
            reader.onload = (f) => {
                const data = f.target.result;
                fabric.Image.fromURL(data, (img) => {
                    // If replacing a placeholder, perform replacement
                    if (placeholderObj) {
                        const center = placeholderObj.getCenterPoint();
                        img.set({
                            left: center.x,
                            top: center.y,
                            originX: 'center',
                            originY: 'center'
                        });
                        // Scale image to fit placeholder logic could go here
                        img.scaleToWidth(placeholderObj.getScaledWidth());
                        this.canvas.remove(placeholderObj);
                    } else {
                        // Center new image
                        img.set({
                            left: this.canvas.width / 2,
                            top: this.canvas.height / 2,
                            originX: 'center',
                            originY: 'center'
                        });
                        img.scaleToWidth(200 * this.canvasScale);
                    }

                    this.canvas.add(img);
                    this.canvas.setActiveObject(img);
                    this.canvas.renderAll();
                    this._saveState();
                });
            };
            reader.readAsDataURL(file);
        };
        input.click();
    },

    // =========================================================================
    // HISTORY (UNDO/REDO)
    // =========================================================================

    _saveState() {
        if (this.historyLocked) return;

        const json = JSON.stringify(this._getDesignJSON());
        const side = this.currentSide;

        // Remove redo stack for current side
        this.history[side] = this.history[side].slice(0, this.historyIndex[side] + 1);
        this.history[side].push(json);
        this.historyIndex[side]++;

        // Limit history size
        if (this.history[side].length > 20) {
            this.history[side].shift();
            this.historyIndex[side]--;
        }
    },

    /**
     * Get canvas JSON with embedded canvas dimensions metadata.
     * This allows us to scale objects proportionally when loading
     * on a canvas with different dimensions (different screen size).
     */
    _getDesignJSON(extraProps) {
        const props = [
            "isGuide", "isPlaceholder", "isDesignAreaBg",
            "selectable", "evented", "hasControls"
        ];
        if (extraProps) props.push(...extraProps);
        const json = this.canvas.toJSON(props);
        // Embed current canvas pixel dimensions so we can scale on load
        json._canvasWidth = this.canvas.getWidth();
        json._canvasHeight = this.canvas.getHeight();
        return json;
    },

    /**
     * Get the complete structured JSON combining both front and back
     * design states. Also updates the active side's state before returning.
     */
    _getCombinedDesignJSON() {
        // Sync active side before fetching the complete state
        if (this.currentSide) {
            this.designStates[this.currentSide] = this._getDesignJSON();
        }

        if (this.hasFrontBack) {
            // Return structured object containing both sides
            return {
                front: this.designStates.front || { objects: [], _canvasWidth: this.baseCanvasWidth, _canvasHeight: this.baseCanvasHeight },
                back: this.designStates.back || { objects: [], _canvasWidth: this.baseCanvasWidth, _canvasHeight: this.baseCanvasHeight }
            };
        } else {
            // Single side fallback, still structured for consistency or just return the object directly
            return this.designStates.front || this._getDesignJSON();
        }
    },


    /**
     * Load a design JSON object onto the current canvas, scaling all object
     * positions and sizes proportionally if the saved canvas dimensions
     * differ from the current ones.  Re-applies background image, visual
     * guide, and clipPath bounding boxes.
     *
     * @param {Object|string} designObj - Fabric JSON (object or string)
     * @param {Function} [callback]     - Optional callback after load
     */
    _loadDesignJSON(designObj, callback) {
        if (typeof designObj === 'string') {
            try { designObj = JSON.parse(designObj); } catch (_e) { return; }
        }
        if (!designObj) return;

        // Strip out any legacy visual guide objects
        if (designObj.objects) {
            designObj.objects = designObj.objects.filter(o => !o.isGuide);
        }

        // --- Proportional scaling ---
        const savedW = designObj._canvasWidth;
        const savedH = designObj._canvasHeight;
        const curW = this.canvas.getWidth();
        const curH = this.canvas.getHeight();
        const needsScale = savedW && savedH && (Math.abs(savedW - curW) > 1 || Math.abs(savedH - curH) > 1);
        const scaleRatioX = needsScale ? curW / savedW : 1;
        const scaleRatioY = needsScale ? curH / savedH : 1;

        if (needsScale && designObj.objects) {
            designObj.objects.forEach(obj => {
                // Scale position
                if (obj.left != null) obj.left *= scaleRatioX;
                if (obj.top != null) obj.top *= scaleRatioY;
                // Scale object dimensions
                if (obj.scaleX != null) obj.scaleX *= scaleRatioX;
                if (obj.scaleY != null) obj.scaleY *= scaleRatioY;
                // Scale radius for circles
                if (obj.type === 'circle' && obj.radius != null) {
                    obj.radius *= Math.min(scaleRatioX, scaleRatioY);
                }
            });
            // Also scale background if present in JSON
            if (designObj.backgroundImage) {
                // We will re-apply our own background image, so remove it
                // to avoid duplicating or mis-scaling
                delete designObj.backgroundImage;
            }
        }

        // Remove embedded canvas dimensions before feeding to Fabric
        delete designObj._canvasWidth;
        delete designObj._canvasHeight;

        this.historyLocked = true;

        // Store current background image reference before loadFromJSON clears it
        const currentBgImage = this.canvas.backgroundImage;

        this.canvas.loadFromJSON(designObj, () => {
            // Restore background image (loadFromJSON may have cleared it)
            if (currentBgImage && !this.canvas.backgroundImage) {
                this.canvas.setBackgroundImage(currentBgImage, this.canvas.renderAll.bind(this.canvas));
            }

            // Re-apply background rect lock and correct clipPath for current side
            const bgRect = this.canvas.getObjects().find(o => o.isDesignAreaBg);
            if (bgRect) {
                bgRect.set({
                    selectable: false,
                    evented: false,
                    hasControls: false,
                    clipPath: this.designAreaClipPath
                });
            }

            // Re-add visual guide
            if (this.visualGuide) {
                // Remove stale guide if one got loaded from JSON
                const staleGuide = this.canvas.getObjects().find(o => o.isGuide);
                if (staleGuide && staleGuide !== this.visualGuide) {
                    this.canvas.remove(staleGuide);
                }
                if (!this.canvas.getObjects().includes(this.visualGuide)) {
                    this.canvas.add(this.visualGuide);
                }
                this.visualGuide.bringToFront();
            }

            // Re-apply clipPath bounding box on custom objects
            this.canvas.getObjects().forEach(obj => {
                if (obj && !obj.isGuide && !obj.isPlaceholder && !obj.isDesignAreaBg && obj.type !== 'activeSelection' && this.designAreaClipPath) {
                    obj.set('clipPath', this.designAreaClipPath);
                }
            });

            this.canvas.requestRenderAll();
            this.historyLocked = false;
            if (callback) callback();
        });
    },

    _onUndo() {
        const side = this.currentSide;
        if (this.historyIndex[side] > 0) {
            this.historyIndex[side]--;
            this.historyLocked = true;
            this._loadDesignJSON(this.history[side][this.historyIndex[side]], () => {
                this.historyLocked = false;
            });
        }
    },

    _onRedo() {
        const side = this.currentSide;
        if (this.historyIndex[side] < this.history[side].length - 1) {
            this.historyIndex[side]++;
            this.historyLocked = true;
            this._loadDesignJSON(this.history[side][this.historyIndex[side]], () => {
                this.historyLocked = false;
            });
        }
    },

    _updatePrice() {
        const totalEl = this.el.querySelector('.o_designer_total_price');
        const unitPriceEl = this.el.querySelector('.o_designer_price');
        if (!totalEl) return;

        const productId = this.productId;
        const variantId = this.variantId || 0;
        const qty = this.quantity;

        // Use core Odoo website_sale route to get the accurate price for this combination and quantity
        rpc('/website_sale/get_combination_info', {
            product_template_id: parseInt(productId),
            product_id: parseInt(variantId),
            combination: [],
            add_qty: qty
        }).then((result) => {
            if (result && result.price !== undefined) {
                const unitPrice = result.price;
                const totalPrice = unitPrice * qty;

                // Format and display the new price
                const currencySymbol = totalEl.dataset.currencySymbol || '';
                const currencyPosition = totalEl.dataset.currencyPosition || 'before';

                const formatPrice = (p) => {
                    let formatted = p.toFixed(result.currency_precision || 2);
                    return currencyPosition === 'after' ? formatted + ' ' + currencySymbol : currencySymbol + ' ' + formatted;
                };

                totalEl.textContent = formatPrice(totalPrice);
                if (unitPriceEl) {
                    unitPriceEl.textContent = formatPrice(unitPrice);
                }
            } else {
                this._fallbackStaticPrice(qty, totalEl, unitPriceEl);
            }
        }).catch((err) => {
            this._fallbackStaticPrice(qty, totalEl, unitPriceEl);
        });
    },

    _fallbackStaticPrice(qty, totalEl, unitPriceEl) {
        // Fallback to static base price calculation
        const totalPrice = this.basePrice * qty;
        const currencySymbol = totalEl.dataset.currencySymbol || '';
        const currencyPosition = totalEl.dataset.currencyPosition || 'before';

        const formatPrice = (p) => {
            let formatted = p.toFixed(2);
            return currencyPosition === 'after' ? formatted + ' ' + currencySymbol : currencySymbol + ' ' + formatted;
        };

        totalEl.textContent = formatPrice(totalPrice);
        if (unitPriceEl && this.basePrice) {
            unitPriceEl.textContent = formatPrice(this.basePrice);
        }
    },

    /**
     * Handle variant selection change in the designer page variant dropdown.
     * Fetches the full variant design config from the server and updates
     * price, canvas background image, design area, limits, and UI.
     */
    async _onVariantChange(ev) {
        const select = ev.currentTarget;
        this.variantId = parseInt(select.value) || 0;
        if (!this.variantId || !this.productId) return;

        try {
            const data = await rpc('/shop/designer/get_variant_info', {
                product_id: parseInt(this.productId),
                variant_id: this.variantId,
            });
            if (data.error) return;

            // --- Update price ---
            const newPrice = parseFloat(data.price);
            if (!isNaN(newPrice)) {
                this.basePrice = newPrice;
                this._updatePrice();
                const priceEl = this.el.querySelector('.o_designer_price');
                if (priceEl) {
                    const currencySymbol = this.el.querySelector('.o_designer_total_price')?.dataset.currencySymbol || '';
                    const currencyPosition = this.el.querySelector('.o_designer_total_price')?.dataset.currencyPosition || 'before';
                    let formatted = newPrice.toFixed(2);
                    if (currencyPosition === 'after') {
                        formatted = formatted + ' ' + currencySymbol;
                    } else {
                        formatted = currencySymbol + ' ' + formatted;
                    }
                    priceEl.textContent = formatted;
                }
            }

            // --- Update limits ---
            this.maxTexts = parseInt(data.design_max_texts) || 0;
            this.maxImages = parseInt(data.design_max_images) || 0;
            this.maxChars = parseInt(data.design_max_characters) || 0;

            // --- Update quantity limits ---
            const qtyInput = this.el.querySelector('.o_designer_quantity');
            if (qtyInput) {
                qtyInput.min = data.min_order_quantity || 1;
                qtyInput.max = data.max_order_quantity || 10000;
            }

            // --- Update production time ---
            const prodTimeEl = this.el.querySelector('.o_designer_price')
                ?.closest('.card-body')
                ?.querySelector('.fa-clock-o')
                ?.closest('p');
            if (prodTimeEl && data.production_time_days) {
                const strong = prodTimeEl.querySelector('strong');
                if (strong) strong.textContent = data.production_time_days;
            }

            // --- Update instructions ---
            const instrCard = this.el.querySelector('.o_designer_instructions_card');
            if (instrCard) {
                const instrBody = instrCard.querySelector('.card-body');
                if (data.design_instruction) {
                    instrBody.innerHTML = data.design_instruction;
                    instrCard.classList.remove('d-none');
                } else {
                    instrCard.classList.add('d-none');
                }
            }

            // --- Update front/back state ---
            const newHasFrontBack = !!data.has_front_back;
            this.hasFrontBack = newHasFrontBack;
            // Show/hide front-back toggle buttons
            this.el.querySelectorAll('.btn-group').forEach(group => {
                const sideBtn = group.querySelector('.o_designer_side');
                if (sideBtn) {
                    group.style.display = newHasFrontBack ? '' : 'none';
                }
            });
            // Also toggle preview modal front/back buttons
            this.el.querySelectorAll('.o_designer_preview_side').forEach(btn => {
                btn.closest('.position-absolute')?.style && (btn.closest('.position-absolute').style.display = newHasFrontBack ? '' : 'none');
            });

            // --- Update canvas background image ---
            const frontUrl = data.front_image_url;
            if (frontUrl && this.canvas) {
                // Reset to front side
                this.currentSide = 'front';
                this.designStates = { front: null, back: null };
                this.history = { front: [], back: [] };
                this.historyIndex = { front: -1, back: -1 };

                // Clear canvas objects
                const objectsToRemove = this.canvas.getObjects().filter(o => !o.isGuide);
                objectsToRemove.forEach(o => this.canvas.remove(o));

                // Add cache-buster to force reload
                const cacheBust = '?t=' + Date.now();

                fabric.Image.fromURL(frontUrl + cacheBust, (img) => {
                    const naturalWidth = img.width;
                    const naturalHeight = img.height;
                    const container = this.el.querySelector('.o_designer_canvas');
                    const containerParent = container.parentElement;
                    const availableWidth = containerParent.clientWidth * 0.95;
                    const availableHeight = containerParent.clientHeight * 0.90;
                    const scaleX = availableWidth / naturalWidth;
                    const scaleY = availableHeight / naturalHeight;
                    const scale = Math.min(scaleX, scaleY);
                    const canvasWidth = naturalWidth * scale;
                    const canvasHeight = naturalHeight * scale;

                    this.canvas.setWidth(canvasWidth);
                    this.canvas.setHeight(canvasHeight);
                    this.baseCanvasWidth = canvasWidth;
                    this.baseCanvasHeight = canvasHeight;
                    this.currentZoom = 1;
                    container.style.width = canvasWidth + 'px';
                    container.style.height = canvasHeight + 'px';

                    img.set({ scaleX: scale, scaleY: scale, originX: 'left', originY: 'top' });
                    this.canvas.setBackgroundImage(img, this.canvas.renderAll.bind(this.canvas));
                    this.canvasScale = scale;
                    this.originalWidth = naturalWidth;
                    this.originalHeight = naturalHeight;

                    // --- Rebuild design area config from variant data ---
                    const createDesignAreaObjects = (pctLeft, pctTop, pctWidth, pctHeight) => {
                        const clipLeft = (pctLeft / 100) * canvasWidth;
                        const clipTop = (pctTop / 100) * canvasHeight;
                        const clipWidth = (pctWidth / 100) * canvasWidth;
                        const clipHeight = (pctHeight / 100) * canvasHeight;
                        const clipPath = new fabric.Rect({
                            left: clipLeft, top: clipTop, width: clipWidth, height: clipHeight,
                            absolutePositioned: true,
                        });
                        clipPath.canvas = this.canvas;
                        const guide = new fabric.Rect({
                            left: clipLeft, top: clipTop, width: clipWidth, height: clipHeight,
                            fill: 'transparent', stroke: 'rgba(59, 130, 246, 0.5)',
                            strokeWidth: 2, strokeDashArray: [5, 5],
                            selectable: false, evented: false, hasControls: false,
                            excludeFromExport: true, isGuide: true,
                        });
                        return { clipPath, guide };
                    };

                    // Remove old guides
                    this.canvas.getObjects().filter(o => o.isGuide).forEach(o => this.canvas.remove(o));

                    const frontObjects = createDesignAreaObjects(
                        data.design_area_left, data.design_area_top,
                        data.design_area_width, data.design_area_height
                    );
                    const backObjects = createDesignAreaObjects(
                        data.design_area_back_left, data.design_area_back_top,
                        data.design_area_back_width, data.design_area_back_height
                    );

                    this.designAreaConfig = {
                        front: { clipPath: frontObjects.clipPath, visualGuide: frontObjects.guide },
                        back: { clipPath: backObjects.clipPath, visualGuide: backObjects.guide },
                    };
                    this.designAreaClipPath = this.designAreaConfig.front.clipPath;
                    this.visualGuide = this.designAreaConfig.front.visualGuide;
                    this.canvas.add(this.visualGuide);

                    // Update the hidden back image element for side toggle
                    const backImgEl = this.el.querySelector('.o_designer_base_image_back');
                    if (data.back_image_url && newHasFrontBack) {
                        if (backImgEl) {
                            backImgEl.src = data.back_image_url + cacheBust;
                        }
                    }

                    this._saveState();
                    this.canvas.requestRenderAll();
                }, { crossOrigin: 'anonymous' });
            }

            // --- Update font selector ---
            if (data.fonts && data.fonts.length) {
                const fontSelect = this.el.querySelector('.o_designer_font_family');
                if (fontSelect) {
                    fontSelect.innerHTML = '';
                    data.fonts.forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f.font_family_name;
                        opt.style.fontFamily = f.font_family_name;
                        opt.textContent = f.name;
                        fontSelect.appendChild(opt);
                        // Load Google fonts dynamically
                        if (f.provider === 'google' && f.css_url) {
                            if (!document.querySelector(`link[href="${f.css_url}"]`)) {
                                const link = document.createElement('link');
                                link.rel = 'stylesheet';
                                link.href = f.css_url;
                                document.head.appendChild(link);
                            }
                        }
                    });
                }
            }

            // --- Update text color swatches ---
            const textColorContainer = this.el.querySelector('.o_designer_text_color_swatches');
            if (textColorContainer && data.text_colors) {
                textColorContainer.innerHTML = '';
                data.text_colors.forEach(tc => {
                    const btn = document.createElement('button');
                    btn.className = 'btn btn-sm o_designer_text_color_swatch';
                    btn.dataset.color = tc.color_code;
                    btn.title = tc.name;
                    btn.style.cssText = `width:26px;height:26px;padding:0;background-color:${tc.color_code};border:2px solid #dee2e6;border-radius:4px;`;
                    textColorContainer.appendChild(btn);
                });
            }

            // --- Update background color swatches ---
            const bgPanel = this.el.querySelector('.o_designer_bg_panel');
            if (bgPanel && data.bg_colors) {
                const bgContainer = bgPanel.querySelector('.d-flex.flex-wrap');
                if (bgContainer) {
                    // Keep the transparent button, replace the rest
                    const transparentBtn = bgContainer.querySelector('[data-color="transparent"]');
                    bgContainer.innerHTML = '';
                    if (transparentBtn) bgContainer.appendChild(transparentBtn);
                    data.bg_colors.forEach(c => {
                        const btn = document.createElement('button');
                        btn.className = 'btn btn-sm o_designer_bg_swatch';
                        btn.dataset.color = c.color_code;
                        btn.title = c.name;
                        btn.style.cssText = `width:32px;height:32px;padding:0;background-color:${c.color_code};border:2px solid #dee2e6;border-radius:4px;`;
                        bgContainer.appendChild(btn);
                    });
                }
            }
        } catch (err) {
            console.error('Error loading variant info:', err);
        }
    },

    _onQtyMinus() {
        const input = this.el.querySelector('.o_designer_quantity');
        const min = parseInt(input.min) || 1;
        const current = parseInt(input.value) || 1;
        if (current <= min) {
            this._showToast(`Minimum order quantity is ${min}.`, 'warning');
            return;
        }
        input.value = current - 1;
        this.quantity = current - 1;
        this._updatePrice();
    },

    _onQtyPlus() {
        const input = this.el.querySelector('.o_designer_quantity');
        const max = parseInt(input.max) || 10000;
        const current = parseInt(input.value) || 1;
        if (current >= max) {
            this._showToast(`Maximum order quantity is ${max}.`, 'warning');
            return;
        }
        input.value = current + 1;
        this.quantity = current + 1;
        this._updatePrice();
    },

    _onQtyChange(ev) {
        const input = ev.currentTarget;
        const min = parseInt(input.min) || 1;
        const max = parseInt(input.max) || 10000;
        let value = parseInt(input.value) || min;

        if (value > max) {
            value = max;
            input.value = max;
            this._showToast(`Maximum order quantity is ${max}.`, 'warning');
        } else if (value < min) {
            value = min;
            input.value = min;
            this._showToast(`Minimum order quantity is ${min}.`, 'warning');
        }

        this.quantity = value;
        this._updatePrice();
    },

    // =========================================================================
    // PREVIEW & DELETE
    // =========================================================================



    _onDeleteClick() {
        if (!this.canvas) return;

        const activeObjects = this.canvas.getActiveObjects();
        if (activeObjects.length) {
            this.canvas.discardActiveObject();
            activeObjects.forEach((obj) => {
                this.canvas.remove(obj);
            });
            this.canvas.renderAll();
            this._saveState();
        }
    },

    /**
     * Handle keyboard events (Delete/Backspace)
     * We attach this to the window or widget root in start() if needed, 
     * but events hash maps to this.el, so user needs focus.
     * Better to attach global listener or ensure focus.
     */
    _onKeydown(ev) {
        if (ev.key === 'Delete' || ev.key === 'Backspace') {
            // Only delete if not editing text
            const activeObj = this.canvas.getActiveObject();
            if (activeObj && !activeObj.isEditing) {
                ev.preventDefault();
                this._onDeleteClick();
            }
        }
    },

    // =========================================================================
    // PREVIEW & DELETE
    // =========================================================================

    /**
     * Helper to get clean image of design regardless of zoom
     */
    _getFullDesignImage(multiplier = 1) {
        if (!this.canvas) return null;

        // Save current state
        const originalVpt = this.canvas.viewportTransform;

        // Temporarily hide the visual guide (design area boundary) so it isn't in the preview
        const guideWasVisible = this.visualGuide && this.visualGuide.visible;
        if (this.visualGuide) {
            this.visualGuide.visible = false;
        }

        // Reset viewport to show full design (identity matrix)
        this.canvas.viewportTransform = [1, 0, 0, 1, 0, 0];

        // Generate image
        const dataUrl = this.canvas.toDataURL({
            format: 'png',
            multiplier: multiplier,
            left: 0,
            top: 0,
            width: this.baseCanvasWidth,
            height: this.baseCanvasHeight
        });

        // Restore state
        this.canvas.viewportTransform = originalVpt;
        if (this.visualGuide) {
            this.visualGuide.visible = guideWasVisible;
        }

        return dataUrl;
    },

    /**
     * Get a clean preview image of a specific side ('front' or 'back').
     * If the requested side is already active, captures directly.
     * Otherwise, temporarily switches to the requested side, captures the
     * image, and restores the original side.
     *
     * Returns a Promise that resolves to the data URL, or null.
     */
    _getDesignImageForSide(side, multiplier = 1) {
        if (!this.canvas) return Promise.resolve(null);
        if (side === 'back' && !this.hasFrontBack) return Promise.resolve(null);

        // Sync current canvas state into designStates
        this.designStates[this.currentSide] = this._getDesignJSON();

        // If already on the requested side, capture directly — no switch needed
        if (this.currentSide === side) {
            return Promise.resolve(this._getFullDesignImage(multiplier));
        }

        const originalSide = this.currentSide;

        return new Promise((resolve) => {
            this._switchSide(side, () => {
                const dataUrl = this._getFullDesignImage(multiplier);
                // Restore the original side
                this._switchSide(originalSide, () => {
                    resolve(dataUrl);
                });
            });
        });
    },

    _onPreviewClick(ev) {

        if (!this.canvas) {

            return;
        }

        // Deselect everything to safely flush active states
        this.canvas.discardActiveObject();
        // Force an immediate synchronous render to ensure the active object state is fully flushed
        // before toDataURL is called, escaping the getRetinaScaling crash issue.
        this.canvas.renderAll();

        // Generate high-quality image ignoring zoom
        const dataUrl = this._getFullDesignImage(2);

        // Show in modal
        const img = this.el.querySelector('#o_designer_preview_image');
        if (img) img.src = dataUrl;

        const modalEl = this.el.querySelector('#o_designer_preview_modal');
        if (modalEl) {


            // Sync preview modal toggles with current canvas side
            if (this.hasFrontBack) {
                const toggles = modalEl.querySelectorAll('.o_designer_preview_side');
                toggles.forEach(btn => {
                    if (btn.dataset.side === this.currentSide) {
                        btn.classList.add('active', 'btn-primary');
                        btn.classList.remove('btn-outline-primary');
                    } else {
                        btn.classList.remove('active', 'btn-primary');
                        btn.classList.add('btn-outline-primary');
                    }
                });
            }

            // Try Bootstrap 5 (native)
            if (typeof window.bootstrap !== 'undefined' && window.bootstrap.Modal) {

                const modal = new window.bootstrap.Modal(modalEl);
                modal.show();
            }
            // Try Bootstrap 4/jQuery (common in Odoo legacy)
            else if (window.$ && window.$(modalEl).modal) {

                window.$(modalEl).modal('show');
            }
            else {

                // Last resort: manually show
                modalEl.classList.add('show');
                modalEl.style.display = 'block';
                document.body.classList.add('modal-open');

                // Add close handler manually
                const closeBtn = modalEl.querySelector('.btn-close, .btn-secondary');
                if (closeBtn) {
                    closeBtn.onclick = () => {
                        modalEl.classList.remove('show');
                        modalEl.style.display = 'none';
                        document.body.classList.remove('modal-open');
                    };
                }
            }
        } else {

        }
    },

    _onDeleteClick(ev) {
        if (!this.canvas) return;

        const activeObjects = this.canvas.getActiveObjects();
        if (activeObjects.length) {
            this.canvas.discardActiveObject();
            activeObjects.forEach((obj) => {
                this.canvas.remove(obj);
            });
            this.canvas.renderAll();
            this._saveState();
        }
    },

    /**
     * Handle keyboard events (Delete/Backspace)
     * We attach this to the window or widget root in start() if needed, 
     * but events hash maps to this.el, so user needs focus.
     * Better to attach global listener or ensure focus.
     */
    _onKeydown(ev) {
        if (ev.key === 'Delete' || ev.key === 'Backspace') {
            // Only delete if not editing text
            const activeObj = this.canvas.getActiveObject();
            if (activeObj && !activeObj.isEditing) {
                // Prevent browser back navigation if Backspace
                if (ev.key === 'Backspace') ev.preventDefault();
                this._onDeleteClick();
            }
        }
    },

    // =========================================================================
    // SAVE & LOAD
    // =========================================================================

    /**
     * Load the customer's previously saved design from the backend.
     * Called automatically on page open.
     */
    _loadSavedDesign() {
        if (!this.customizationId) return;

        rpc('/shop/designer/load_saved', {
            product_id: parseInt(this.productId),
            variant_id: this.variantId || 0,
        }).then((result) => {
            if (!result || !result.design_json) return;

            // Store the customization id for future saves
            this.customizationId = result.customization_id;

            // Restore quantity
            if (result.quantity && result.quantity > 1) {
                const qtyInput = this.el.querySelector('.o_designer_quantity');
                if (qtyInput) {
                    qtyInput.value = result.quantity;
                    this.quantity = result.quantity;
                    this._updatePrice();
                }
            }

            // Parse and restore canvas state structure
            let designObj;
            try {
                designObj = typeof result.design_json === 'string' ? JSON.parse(result.design_json) : result.design_json;
            } catch (e) {

                return;
            }

            if (this.hasFrontBack && designObj.front !== undefined) {
                // It's a combined object
                this.designStates.front = designObj.front;
                this.designStates.back = designObj.back || null;

                // Load whatever side is currently active (defaults to 'front')
                this._loadDesignJSON(this.designStates[this.currentSide], () => {
                    this._saveState();
                });
            } else {
                // Legacy or single-sided design format
                if (this.currentSide) {
                    this.designStates[this.currentSide] = designObj;
                }
                this._loadDesignJSON(designObj, () => {
                    this._saveState();
                });
            }
        });
    },

    /**
     * Save the current design to the backend without adding to cart.
     * Shows a brief toast notification on success.
     */
    async _onSaveDesign() {
        if (!this.canvas) return;

        const saveBtn = this.el.querySelector('.o_designer_save');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i>';
        }

        // Deselect to get clean snapshot
        this.canvas.discardActiveObject();
        this.canvas.renderAll();

        const designData = JSON.stringify(this._getCombinedDesignJSON());

        // Generate side-aware preview images
        const previewImage = await this._getDesignImageForSide('front', 1);
        const previewImageBack = await this._getDesignImageForSide('back', 1);

        rpc('/shop/designer/save', {
            product_id: parseInt(this.productId),
            design_data: designData,
            quantity: this.quantity,
            customization_id: this.customizationId,
            variant_id: this.variantId || 0,
            preview_image: previewImage,
            preview_image_back: previewImageBack,
        }).then((result) => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa fa-floppy-o me-1"></i>';
            }
            if (result && result.success) {
                this.customizationId = result.customization_id;
                this._showToast('Design saved!', 'success');
            } else {
                this._showToast('Could not save design.', 'danger');
            }
        }).catch(() => {
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa fa-floppy-o me-1"></i>';
            }
            this._showToast('Could not save design.', 'danger');
        });
    },

    /**
     * Show a brief Bootstrap toast notification.
     */
    _showToast(message, type = 'success') {
        // Remove any existing toast
        const existing = this.el.querySelector('.o_designer_toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = `o_designer_toast alert alert-${type} shadow position-fixed`;
        toast.style.cssText = 'bottom: 1.5rem; right: 1.5rem; z-index: 9999; min-width: 220px; opacity: 0; transition: opacity 0.3s;';
        toast.innerHTML = `<i class="fa fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>${message}`;
        document.body.appendChild(toast);

        // Fade in
        requestAnimationFrame(() => { toast.style.opacity = '1'; });

        // Fade out after 2.5 s
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 350);
        }, 2500);
    },

    async _onAddToCart() {
        // Deselect to get clean snapshot
        this.canvas.discardActiveObject();
        this.canvas.renderAll();

        // Collect data
        const designData = JSON.stringify(this._getCombinedDesignJSON());

        // Generate side-aware preview images
        const previewImage = await this._getDesignImageForSide('front', 1);
        const previewImageBack = await this._getDesignImageForSide('back', 1);

        // 1. Save the design first (upsert)
        rpc('/shop/designer/save', {
            product_id: parseInt(this.productId),
            design_data: designData,
            quantity: this.quantity,
            customization_id: this.customizationId,
            variant_id: this.variantId || 0,
            preview_image: previewImage,
            preview_image_back: previewImageBack,
        }).then((saveResult) => {
            if (saveResult.success && saveResult.customization_id) {
                this.customizationId = saveResult.customization_id;
                // 2. Add to cart with the saved customization ID
                rpc('/shop/designer/add_to_cart', {
                    product_id: parseInt(this.productId),
                    customization_id: saveResult.customization_id,
                    quantity: this.quantity,
                    variant_id: this.variantId || 0,
                    preview_image: previewImage,
                    preview_image_back: previewImageBack,
                }).then((cartResult) => {
                    if (cartResult.success) {
                        window.location.href = '/shop/cart';
                    } else {
                        this.call("dialog", "add", WarningDialog, {
                            title: "Notice",
                            message: 'Could not add to cart: ' + (cartResult.error || 'Unknown error')
                        });
                    }
                });
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: "Notice",
                    message: 'Could not save design: ' + (saveResult.error || 'Unknown error')
                });
            }
        });
    },

    _applyZoom() {
        if (!this.canvas) return;

        // 1. Scale the fabric internal camera
        this.canvas.setZoom(this.currentZoom);

        // 2. Scale the fabric canvas HTML elements physically so scrollbars appear
        const newWidth = this.baseCanvasWidth * this.currentZoom;
        const newHeight = this.baseCanvasHeight * this.currentZoom;
        this.canvas.setDimensions({ width: newWidth, height: newHeight });

        // 3. Scale the Odoo wrapper container to match
        const container = this.el.querySelector('.o_designer_canvas');
        if (container) {
            container.style.width = newWidth + 'px';
            container.style.height = newHeight + 'px';
        }

        this.canvas.requestRenderAll();
    },

    _onZoomIn() {
        const newZoom = this.currentZoom * 1.1;
        // Limit max zoom
        if (newZoom > 5) return;

        this.currentZoom = newZoom;
        this._applyZoom();
    },

    _onZoomOut() {
        const newZoom = this.currentZoom / 1.1;
        // Limit min zoom
        if (newZoom < 0.1) return;

        this.currentZoom = newZoom;
        this._applyZoom();
    },

    _onZoomFit() {
        this.currentZoom = 1;
        this.canvas.setViewportTransform([1, 0, 0, 1, 0, 0]);
        this._applyZoom();
    },

    /**
     * Clear all user-added objects from the current side's canvas.
     * Keeps the visual guide and background image intact.
     */
    _onClearAll() {
        if (!this.canvas) return;
        if (!confirm('Clear all objects from the current side? This cannot be undone.')) return;

        // Remove all objects except the visual guide
        const objectsToRemove = this.canvas.getObjects().filter(
            o => !o.isGuide
        );
        objectsToRemove.forEach(o => this.canvas.remove(o));

        // Reset the background swatch highlight
        this.el.querySelectorAll('.o_designer_bg_swatch').forEach(s => {
            s.style.borderColor = '#dee2e6';
        });

        this.canvas.discardActiveObject();
        this.canvas.requestRenderAll();
        this._saveState();
    },

    // Switch between front and back views
    _onSideToggle(ev) {
        if (!this.hasFrontBack || !this.canvas) return;

        const btn = ev.currentTarget;
        const targetSide = btn.dataset.side;

        if (this.currentSide === targetSide) return; // Already on this side

        // Find the main canvas toggle button to update UI
        const canvasToggleBtn = this.el.querySelector(`.o_designer_side[data-side="${targetSide}"]`);

        this._switchSide(targetSide, () => {
            // Update canvas UI buttons
            this.el.querySelectorAll('.o_designer_side').forEach(el => el.classList.remove('active', 'btn-primary'));
            this.el.querySelectorAll('.o_designer_side').forEach(el => el.classList.add('btn-outline-primary'));
            if (canvasToggleBtn) {
                canvasToggleBtn.classList.remove('btn-outline-primary');
                canvasToggleBtn.classList.add('btn-primary', 'active');
            }
        });
    },

    _onPreviewSideToggle(ev) {
        if (!this.hasFrontBack || !this.canvas) return;

        const btn = ev.currentTarget;
        const targetSide = btn.dataset.side;

        if (this.currentSide === targetSide) return; // Already on this side

        // Optional: show loading state on image
        const img = this.el.querySelector('#o_designer_preview_image');
        if (img) img.style.opacity = '0.5';

        // Update modal UI buttons immediately
        const modalEl = this.el.querySelector('#o_designer_preview_modal');
        if (modalEl) {
            modalEl.querySelectorAll('.o_designer_preview_side').forEach(el => {
                el.classList.remove('active', 'btn-primary');
                el.classList.add('btn-outline-primary');
            });
        }
        btn.classList.remove('btn-outline-primary');
        btn.classList.add('btn-primary', 'active');

        // Also sync the canvas UI buttons behind the modal
        const canvasToggleBtn = this.el.querySelector(`.o_designer_side[data-side="${targetSide}"]`);
        if (canvasToggleBtn) {
            this.el.querySelectorAll('.o_designer_side').forEach(el => el.classList.remove('active', 'btn-primary'));
            this.el.querySelectorAll('.o_designer_side').forEach(el => el.classList.add('btn-outline-primary'));
            canvasToggleBtn.classList.remove('btn-outline-primary');
            canvasToggleBtn.classList.add('btn-primary', 'active');
        }

        this._switchSide(targetSide, () => {
            // Generate new preview image ignoring zoom
            const dataUrl = this._getFullDesignImage(2);
            if (img) {
                img.src = dataUrl;
                img.style.opacity = '1';
            }
        });
    },

    _switchSide(targetSide, callback) {
        // 1. Serialize and save current side's state
        this.designStates[this.currentSide] = this._getDesignJSON();

        // 2. Swap design area objects (clip path + visual guide)
        //    Remove current side's visual guide from canvas
        if (this.visualGuide && this.canvas.getObjects().includes(this.visualGuide)) {
            this.canvas.remove(this.visualGuide);
        }

        // 3. Update current side
        this.currentSide = targetSide;

        // 4. Activate the target side's design area config
        if (this.designAreaConfig && this.designAreaConfig[targetSide]) {
            this.designAreaClipPath = this.designAreaConfig[targetSide].clipPath;
            this.visualGuide = this.designAreaConfig[targetSide].visualGuide;
        }

        // 5. Change background image
        const imgElement = targetSide === 'front'
            ? this.el.querySelector('.o_designer_base_image')
            : this.el.querySelector('.o_designer_base_image_back');

        if (imgElement) {
            const bgSrc = imgElement.src;
            fabric.Image.fromURL(bgSrc, (img) => {
                // Apply the existing scale factor to the new background
                img.set({
                    scaleX: this.canvasScale,
                    scaleY: this.canvasScale,
                    originX: 'left',
                    originY: 'top'
                });

                this.canvas.setBackgroundImage(img, () => {
                    // 6. Clear current objects and load the new side's state (if any)
                    const targetState = this.designStates[targetSide];

                    if (targetState) {
                        // Temporarily bypass history saving while loading
                        this.historyLocked = true;

                        this._loadDesignJSON(targetState, () => {
                            this.historyLocked = false;
                            this.canvas.requestRenderAll();

                            // Ensure history stack is accurate for this side
                            if (this.history[targetSide].length === 0) {
                                this._saveState(); // Initialize history for this side
                            }
                            if (callback) callback();
                        });
                    } else {
                        // First time visiting this side: clear objects except guides
                        const objectsToRemove = this.canvas.getObjects().filter(o => !o.isGuide && !o.isPlaceholder && !o.isDesignAreaBg);
                        objectsToRemove.forEach(o => this.canvas.remove(o));

                        // Add the new side's visual guide
                        if (this.visualGuide && !this.canvas.getObjects().includes(this.visualGuide)) {
                            this.canvas.add(this.visualGuide);
                            this.visualGuide.bringToFront();
                        }

                        this.canvas.requestRenderAll();
                        this._saveState(); // Initialize history for this side
                        if (callback) callback();
                    }
                });
            });
        }
    },

    /**
     * Save the current canvas design as a reusable template (admin only).
     */
    async _onSaveAsTemplate() {
        if (!this.canvas) return;

        const isEditing = !!this.editingTemplateId;
        const defaultName = isEditing ? this.editingTemplateName : '';
        const promptMsg = isEditing
            ? `Update template name (or keep as-is):`
            : 'Enter a name for this template:';

        const templateName = window.prompt(promptMsg, defaultName);
        if (templateName === null) return; // User cancelled

        const btn = this.el.querySelector('.o_designer_save_template');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<i class="fa fa-spinner fa-spin me-1"></i> Saving...';
        }

        // Deselect active objects to get clean snapshot
        this.canvas.discardActiveObject();
        this.canvas.renderAll();

        // Generate side-aware preview images
        const previewImage = await this._getDesignImageForSide('front', 1);
        const previewImageBack = await this._getDesignImageForSide('back', 1);

        // Serialize canvas JSON with both sides
        const designData = JSON.stringify(this._getCombinedDesignJSON());

        const productId = this.el.querySelector('.o_designer_canvas')?.dataset?.productId;

        // Choose route based on editing state
        const route = isEditing
            ? '/shop/designer/update_template'
            : '/shop/designer/save_as_template';

        const params = isEditing
            ? {
                template_id: this.editingTemplateId,
                design_data: designData,
                template_name: templateName || defaultName,
                preview_image: previewImage,
                preview_image_back: previewImageBack,
            }
            : {
                product_id: productId,
                design_data: designData,
                template_name: templateName,
                preview_image: previewImage,
                preview_image_back: previewImageBack,
            };

        rpc(route, params).then((result) => {
            if (btn) {
                btn.disabled = false;
            }

            if (result.success) {
                const action = isEditing ? 'updated' : 'saved';
                this.call("dialog", "add", WarningDialog, {
                    title: "Success",
                    message: `Template "${result.template_name}" ${action} successfully!`
                });
                // Clear editing state after successful update
                if (isEditing) {
                    this._clearTemplateEditing();
                }
                // Refresh templates panel
                this._loadTemplates();
            } else {
                this.call("dialog", "add", WarningDialog, {
                    title: "Error",
                    message: 'Could not save template: ' + (result.error || 'Unknown error')
                });
            }
            this._updateTemplateButton();
        }).catch((err) => {
            if (btn) {
                btn.disabled = false;
            }
            this._updateTemplateButton();
            this.call("dialog", "add", WarningDialog, {
                title: "Error",
                message: 'Failed to save template: ' + (err.message || err)
            });
        });
    },

    /**
     * @override
     */
    destroy() {
        if (this.canvas) {
            this.canvas.dispose();
        }
        this._super(...arguments);
    }
});

/**
 * Small widget on the product page to redirect to the designer
 * with the currently selected variant ID appended to the URL.
 */
publicWidget.registry.DesignerVariantRedirect = publicWidget.Widget.extend({
    selector: '#o_designer_btn_link',
    events: {
        'click': '_onDesignerBtnClick',
    },
    _onDesignerBtnClick(ev) {
        const $container = this.$el.closest('#product_detail, form, body');
        const variantInput = $container.find('input.product_id[name="product_id"]')[0];
        if (variantInput) {
            ev.preventDefault();
            const href = this.el.getAttribute('href');
            window.location.href = href + '?variant_id=' + variantInput.value;
        }
    },
});
