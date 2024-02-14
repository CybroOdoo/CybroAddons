 /** @odoo-module **/
import { registry } from "@web/core/registry";
import { isBinarySize } from "@web/core/utils/binary";
import { url } from "@web/core/utils/urls";
import {ImageField, imageCacheKey, imageField} from "@web/views/fields/image/image_field";
import { useRef, useEffect } from "@odoo/owl";
const { useState } = owl;

 /**
  * Create canvas for adding 3D model
  */
export class Field3D extends ImageField {
   setup(){
    super.setup();
    this.useRef = useRef("field_3d")
    this.elId = `#${this.props.name}_el`
    this.state = useState({
        isValid: true,
        value: url('/model_viewer_widget/static/src/assets/3d.glb')
    });
    this.canvasEl = '<canvas class="view3d-canvas"/>'
    useEffect(() => {
        this.createCanvas()
        if (isBinarySize(this.props.record.data[this.props.name])) {
            this.state.value = url("/web/content", {
                model: this.props.record.resModel,
                id: this.props.record.resId,
                field: this.props.name,
                unique: imageCacheKey(this.rawCacheKey),
            });
        } else if(this.props.record.data[this.props.name]){
            this.state.value = `data:model/gltf-binary;base64, ${this.props.record.data[this.props.name]}`
        }
        this.view3D = new View3D(this.elId, {
            src: this.state.value
        });
    })
   }
    /**
  * At the time of removing file, a default 3D model will be displayed
  */
   onFileRemove(){
    super.onFileRemove();
    this.createCanvas()
    this.state.value = url('/model_viewer_widget/static/src/assets/3d.glb');
    if(this.view3D){
        this.view3D.load(this.state.value)
    }
   }
   /**
  * Create canvas for adding 3D model
  */
   createCanvas(){
       var elem = this.useRef.el.querySelector(this.elId)
       const prevCanvas = this.useRef.el.querySelector('canvas');
       if(prevCanvas)
           elem.removeChild(prevCanvas)
       const canvas = document.createElement('canvas');
       canvas.width = 600;
       canvas.height = 500;
       canvas.classList.add('view3d-canvas')
       elem.appendChild(canvas);
   }
   /**
  *  At the time of uploading file, the uploaded 3D model will be displayed
  */
    async onFileUploaded(info) {
       super.onFileUploaded(info)
       this.createCanvas()
       console.log(info)
       this.props.record.update({ [this.props.name]: info.data });
    }
}

Field3D.acceptedFileExtensions = "*"
Field3D.template = "Field3DWidget"

export const image3D = {
     ...imageField,
    component: Field3D,
};


registry.category("fields").add("3D_widget", image3D);
