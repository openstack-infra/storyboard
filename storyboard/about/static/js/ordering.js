var ARROW_TEMPLATE = "&nbsp<i class='icon-arrow-$type'></i>";

function bindOrderingHandlers() {
    $(".sortable-column a").click(function() {
        var $this = $(this);
        var order_key = $this.parent("th").attr("data-order-key");

        setTaskOrdering(order_key);
    });
}

function addOrderArrow(field, type) {
    $(".sortable-column[data-order-key=" + field +"] a").append(
        ARROW_TEMPLATE.replace("$type", type)
    );
}

function setTaskOrdering(field) {
    prepareAJAX();
    $.post("/project/setorder/", {"page_type": page_type,
                                  "order_field": field})
        .success(function() { window.location.reload(); })
}
