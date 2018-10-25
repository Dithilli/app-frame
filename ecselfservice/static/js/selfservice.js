$(function () {
  $('[data-toggle="tooltip"]').tooltip()
  $('[data-toggle="popover"]').popover({
    html: true,
    content: function() {
      let poNode = $(this.parentNode).find(".popover");
      return poNode.length > 0 ? $(poNode[0]).html() : "";
    }
  })
})
