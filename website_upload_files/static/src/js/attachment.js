const btn = document.getElementById('add_attachment');
if(btn){
    btn.addEventListener('click', () => {
      console.log("success")
      $('#add_sale_attachment').modal('hide');
    });
}
