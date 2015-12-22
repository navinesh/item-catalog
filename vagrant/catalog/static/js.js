$(window).load(function() {
  $("#search").keyup(function() {
    var searchField = $('#search').val();
    var regex = new RegExp(searchField, "i");
    var q = $("#search").val();
    $.ajax({
      dataType: "json",
      url: "/items.json",
      success: function(result) {
        $("#results").empty();
        $("#results").append("<p>Results for <b>" + q + "</b></p>");
        $.each(result, function(i, item) {
          for (var x = 0; x < item.length; x++) {
            if ((item[x].name.search(regex) != -1) || (item[x].description.search(regex) != -1)) {
              $("#results").append("<div class='panel panel-default'>" + "<div class='panel-body'>" + "<div class='col-md-2'>" + "<img class='img-thumbnail' alt='Item image' height='100' width='100' src='http://localhost:8000/" + encodeURIComponent(item[x].image_name) + "'>"  + "</a></div>" + "<div class='col-md-10'>" + '<h4>' + item[x].name + '</h4>' + '<i>Description:</i>' + " " + item[x].description + "</div></div></div>");
            }
            if (q == ''){
              $("#results").empty();
            }
          }
        });
      }
    });
  });
});
