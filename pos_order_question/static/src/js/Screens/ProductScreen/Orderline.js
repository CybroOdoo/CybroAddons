/** @odoo-module **/
//    Extending pos order line
    const Orderline = require('point_of_sale.Orderline');
    const Registries = require('point_of_sale.Registries');
    const PosQuesOrderline = Orderline =>
        class extends Orderline {
        AddOptions(){
    //        This function will add questions of that of product into the popup.
           var ProductQuestions = this.props.line.product.order_question_ids
           var OrderQuestions = this.env.pos.order_questions
           let question = [];
            for (var i = 0, len = OrderQuestions.length; i < len; i++){
                for (var j=0, leng = ProductQuestions.length; j<leng; j++){
                    if (OrderQuestions[i].id==ProductQuestions[j]){
                        question.push(OrderQuestions[i].name)
                    }
                }
            }
           if (question.length != 0){
               this.showPopup('OrderQuestionPopup', {
                   confirmText: 'Ok',
                   cancelText: 'Cancel',
                   title: 'Extra...',
                   body: question,
               });
           }
           else{
               this.showPopup('OrderQuestionPopup', {
                   confirmText: 'Ok',
                   cancelText: 'Cancel',
                   title: 'Add Options to Select...',
               });
           }
        }
    }
Registries.Component.extend(Orderline, PosQuesOrderline);
return Orderline;
