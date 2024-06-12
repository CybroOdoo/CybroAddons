/** @odoo-module **/

    // Import required modules
    import publicWidget from "@web/legacy/js/public/public_widget";
    let canvas = new fabric.Canvas('tshirt-canvas');
    var count = 0;
    // Event listener for the "Delete" key
    document.addEventListener("keydown", function(event){
        var value = event.key;
        if (value=="Delete"){
            canvas.remove(canvas.getActiveObject());
        }
    });
    // Define a custom widget
    publicWidget.registry.canvasWidget = publicWidget.Widget.extend({
    selector: '#product_detail',
    events: {
        'change #product-design': '_onChangeSelect',
        'click .design_save': '_onSave',
        'click #product_customize_btn': '_addProductDesign',
    },
    // Event handler for the change event on the product-design element
    _onChangeSelect: function(){
        var selectedOption = this.$el.find('#product-design').val().toString();
        var design_image = new Image();
        design_image.src = '/web/image/product.design/' + selectedOption + '/product_design'
        design_image.onload = function () {
                        var image = new fabric.Image(design_image);
                        image.scaleToHeight(100);
                        image.scaleToWidth(100);
                        canvas.centerObject(image);
                        canvas.add(image);
                        canvas.renderAll();
                    };
        },
    // Event handler for the click event on elements with the design_save class
    _onSave: function(design_image){
        var node = design_image.delegateTarget.lastElementChild.querySelector('#tshirt-div');
        domtoimage.toPng(node).then(function (dataUrl) {
        var img = new Image();
        img.classList.add("design_image_doc");
        img.src = dataUrl;
        document.body.appendChild(img);
        alert('Saved your customized Image!!!!!!, Now you can Add it in to the cart')
        })
    },
    // Event handler for the click event on the product_customize_btn element
    _addProductDesign: function(ev){
        count++
        if (count%2 == 0){
           ev.target.offsetParent.nextElementSibling.classList.add("d-none");
        }
        else{
        ev.target.offsetParent.nextElementSibling.classList.remove("d-none");
        }
    },
});
