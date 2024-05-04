  var modal = document.getElementById("myModal");
  var openModalBtn = document.getElementById("openModalBtn");
  var closeModal = document.getElementById("closeModal");

  openModalBtn.addEventListener("click", function() {
            modal.style.display = "block";
 });
  closeModal.addEventListener("click", function() {
      modal.style.display = "none";
  });
  window.addEventListener("click", function(event) {
      if (event.target == modal) {
          modal.style.display = "none";
      }
  });
  var review_star;

  function getStar() {
      const starInputs = document.querySelectorAll('.stars input[type="radio"]');
      let selectedValue;
      starInputs.forEach((input) => {
          if (input.checked) {
                selectedValue = input.value;
          }
      });
      review_star = selectedValue
  }

  function myFunction() {
      var pos_order = []
      var review_text = document.getElementById("productRating").value;
      pos_order.push({
          'review_text': review_text,
          'review_star': review_star,
          'session': document.querySelector('.session_id').value,
          'partner_id': document.querySelector('.partner_id').value,
          'order_name': document.querySelector('.order_name').value
      })
      var review = JSON.stringify(pos_order)
      $.ajax({
          url: '/customer/review/' + review,
          type: 'post',
          contentType: 'Application/json',
          dataType: 'Application/json',
          data: JSON.stringify({
              main: review
          }),
          success: function(data) {},
          error: function(data) {}
      })
      modal.style.display = "none";
  }

