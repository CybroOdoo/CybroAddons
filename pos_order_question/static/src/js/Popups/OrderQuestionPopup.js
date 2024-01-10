/** @odoo-module **/
//    Extend AbstractAwaitablePopup to add OrderQuestionPopup
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    class OrderQuestionPopup extends AbstractAwaitablePopup {
        setup() {
            super.setup();
        }
        _onClickCheck(){
        //    This function will work when clicking on checkboxes.It will add questions of enabled check boxed into the list.
            this.QuestionList = [];
            var CheckButton = document.getElementById("SecDiv");
            for (var j=0, leng = CheckButton.childNodes.length- 1; j<leng; j++){
                if (CheckButton.childNodes[j].firstChild.checked == true){
                    this.QuestionList.push(CheckButton.childNodes[j].textContent)
                }
            }
        }
        async confirm(){
        //   This function will work when clicking on ok button in the popup.It will add selected questions into order lines.
            const selectedOrderline = this.env.pos.get_order().get_selected_orderline();
            selectedOrderline.QuestionList = this.QuestionList
            this.cancel();
        }
    }
    OrderQuestionPopup.template = 'OrderQuestionPopup';
    OrderQuestionPopup.defaultProps= { confirmKey: false };
    Registries.Component.add(OrderQuestionPopup);
