/** @odoo-module **/

    import { PivotRenderer } from "@web/views/pivot/pivot_renderer";
    import { PivotController } from "@web/views/pivot/pivot_controller";
    import { useService } from "@web/core/utils/hooks";
    import { patch } from '@web/core/utils/patch';
    const { useExternalListener, useEffect } = owl;

    patch(PivotRenderer.prototype,'pivot_render.patch',{
        setup() {
            this._super.apply();
            this.orm = useService("orm");
            this.isMouseDown = false;
            this.startRowIndex = null;
            this.startCellIndex = null;
            useExternalListener(document, 'mouseup', this.mouse_up_function)
            useEffect(() => {
                this.set_default_rules()
            })
        },

        async set_default_rules(){
//            function for default rules to be applied on the pivot table
            var self = this
            var viewId = this.env.config.viewId
            var model = this.env.searchModel.resModel
            await this.orm.call("conditional.rules","search_read", [],{
                domain: [['model_id','=',model],['view_id','=',viewId]],
            }).then(function(res){
                self.conditional_rules = res
            })
            var cells = this.__owl__.bdom.el.querySelectorAll('td')
            cells.forEach(function(data){
                data.style.backgroundColor = "#f8f9fa"
                data.style.color = "black"
            })
            $(this.__owl__.bdom.el.querySelectorAll(
            '.o_pivot.table-responsive table')).find(
            ".selected_cell").removeClass("selected_cell");
            $(this.__owl__.bdom.parentEl.parentElement).find(
            '.conditional_button').css({display:"none"})
            $(this.__owl__.bdom.parentEl.parentElement).find(
            '.conditional_container').css({display:"none"})

            for (let i = 0, len = this.conditional_rules.length; i < len; i++){
                var condition = this.conditional_rules[i].rule
                var condition_val = this.conditional_rules[i].value
                var second_condition_val = this.conditional_rules[i].second_value
                var color_val = this.conditional_rules[i].color
                var text_color_val = this.conditional_rules[i].text_color

                for (let j = 0, len = cells.length; j < len; j++){
                    var cell_val = cells[j].innerText
                    if(cell_val){
                        cell_val = cell_val.replace(',','')
                    }
                    if(condition == 'less_than'){
                        if(parseFloat(condition_val)>parseFloat(cell_val)){
                            cells[j].classList.remove("bg-100")
                            cells[j].style.backgroundColor = color_val
                            cells[j].style.color = text_color_val
                        }
                    }
                    if(condition == "greater_than"){
                        if(parseFloat(condition_val)< parseFloat(cell_val)){
                            cells[j].classList.remove("bg-100")
                            cells[j].style.backgroundColor = color_val
                            cells[j].style.color = text_color_val
                        }
                    }
                    if(condition == "is_empty"){
                        if(cells[j].innerText == ""){
                            cells[j].classList.remove("bg-100")
                            cells[j].style.backgroundColor = color_val
                            cells[j].style.color = text_color_val
                        }
                    }
                    if(condition == "in_between"){
                        if(parseFloat(cell_val)> parseFloat(condition_val) && parseFloat(cell_val)< parseFloat(second_condition_val)){
                            cells[j].classList.remove("bg-100")
                            cells[j].style.backgroundColor = color_val
                            cells[j].style.color = text_color_val
                        }
                    }
                }
            }
        },
        conditional_formattoo(e){
        // function for selecting table columns and adding and removing
//         classes
            if (e.target.localName == 'td' || e.target.className == 'o_value'){
                this.isMouseDown = true;
                var cell;
                if(e.target.className == 'o_value'){
                    cell = e.target.parentElement;
                }else{
                    cell = e.target
                }
                $(this.__owl__.bdom.el.querySelectorAll(
                '.o_pivot.table-responsive table')).find(".selected_cell"
                ).removeClass("selected_cell"); // deselect everything
                cell.className = 'selected_cell prevent-select'
                this.startCellIndex = cell.cellIndex;
                this.startRowIndex = cell.parentElement.cellIndex;
                return false;
            }
        },


        mouse_over_function(e){
//        function for selecting table columns
            if (!this.isMouseDown) return;
            if (e.target.localName == 'td' || e.target.className == 'o_value'){
                var cell = e.target.parentElement;
                if(e.target.className == 'o_value'){
                    cell = e.target.parentElement;
                }else{
                    cell = e.target
                }
                cell.classList.add("selected_cell")
                $(this.__owl__.bdom.parentEl.parentElement).find(
            '.conditional_button').css({display:'block'})
            }
        },

        mouse_up_function(){
//        function for changing variable value to stop table cell selection
            this.isMouseDown = false;
        },

        display_field(){
//        function for hiding and showing input fields inside popup window
            var condition = $(this.__owl__.bdom.el.querySelectorAll(
                '.condition_select')).val()
            if(this.__owl__.bdom.el.querySelectorAll(
                '.validation-error')[0].style.display == "inline"){
                this.__owl__.bdom.el.querySelectorAll(
                '.validation-error')[0].style.display = "none";
                }
            $(this.__owl__.bdom.el.querySelectorAll(
                '#condition_val'))[0].value = ''
            $(this.__owl__.bdom.el.querySelectorAll(
                '#secondcondition_val'))[0].value = ''
            if(condition == 'in between'){
                $(this.__owl__.bdom.el.querySelectorAll(
                '#secondcondition_val')).css({display:'block'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#value_label')).css({display:'block'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#sub_input_container2')).css({display:'flex'})
            }else{
                $(this.__owl__.bdom.el.querySelectorAll(
                '#secondcondition_val')).css({display:'none'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#value_label')).css({display:'none'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#sub_input_container2')).css({display:'none'})
            }
            if(condition === 'null'){
                $(this.__owl__.bdom.el.querySelectorAll(
                '#condition_val')).css({display:'none'})

                $(this.__owl__.bdom.el.querySelectorAll(
                '#value_label1')).css({display:'none'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#sub_input_container1')).css({display:'none'})
            }else{
                $(this.__owl__.bdom.el.querySelectorAll(
                '#condition_val')).css({display:'block'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#value_label1')).css({display:'block'})
                $(this.__owl__.bdom.el.querySelectorAll(
                '#sub_input_container1')).css({display:'flex'})
            }
        },
        set_rule(){
//        function for applying rules through popup window
            var condition = $(this.__owl__.bdom.el.querySelectorAll(
                '.condition_select')).val()
            var color_val = $(this.__owl__.bdom.el.querySelectorAll(
                '.colorpicker')).val()
            var text_color_val = $(this.__owl__.bdom.el.querySelectorAll(
                '.text_color')).val()
            var cells = $(this.__owl__.bdom.el.querySelectorAll(
                '.selected_cell'))
            var condition_val = $(this.__owl__.bdom.el.querySelectorAll(
                '#condition_val')).val()
            var second_condition_val = $(this.__owl__.bdom.el.querySelectorAll(
                '#secondcondition_val')).val()
            this.__owl__.bdom.el.querySelectorAll(
                '#condition_val')[0].value = ''
            this.__owl__.bdom.el.querySelectorAll(
                '#secondcondition_val')[0].value = ''
            if(condition == 'in between'){
                if(condition_val > second_condition_val){
                    $(this.__owl__.bdom.el.querySelectorAll(
                '.validation-error')).css({display:'inline'})
                    return
                }
            }
            for (let i = 0, len = cells.length; i < len; i++){
                var cell_val = cells[i].innerText
                if(cell_val){
                    cell_val = cell_val.replace(',','')
                }
                if(condition == 'less than'){
                    if(parseFloat(condition_val)>parseFloat(cell_val)){
                        cells[i].classList.remove("bg-100")
                        cells[i].style.backgroundColor = color_val
                        cells[i].style.color = text_color_val
                    }
                }
                if(condition == 'greater than'){
                    if(parseFloat(condition_val)< parseFloat(cell_val)){
                        cells[i].classList.remove("bg-100")
                        cells[i].style.backgroundColor = color_val
                        cells[i].style.color = text_color_val
                    }
                }
                if(condition == "null"){
                    if(cells[i].innerText == ""){
                        cells[i].classList.remove("bg-100")
                        cells[i].classList.remove("bg-100")
                        cells[i].style.backgroundColor = color_val
                        cells[i].style.color = text_color_val
                    }
                }
                if(condition == 'in between'){
                    if(parseFloat(cell_val)> parseFloat(condition_val) && parseFloat(cell_val)< parseFloat(second_condition_val)){
                        cells[i].classList.remove("bg-100")
                        cells[i].style.backgroundColor = color_val
                        cells[i].style.color = text_color_val
                    }
                }
            }
        },

    });
    patch(PivotController.prototype, 'PivotController.Patch', {
        conditional_format_tab(){
//        This function is called to display the conditional formatting
//        window/wizard in the UI.
            $(this.__owl__.bdom.el.querySelectorAll(".conditional_container")).css({display:"block"})
            this.__owl__.bdom.el.querySelectorAll("#condition_val")[0].value = ''
            this.__owl__.bdom.el.querySelectorAll("#secondcondition_val")[0].value = ''
            if(this.__owl__.bdom.el.querySelectorAll(
                '.validation-error')[0].style.display == "inline"){
                this.__owl__.bdom.el.querySelectorAll(
                '.validation-error')[0].style.display = "none";
                }
        },
    });
