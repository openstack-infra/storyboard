//Set pagination dropdown to value in request
function setPaginationDropdownValue(value) {
    var readable_value = value  + " tasks per page";
    if (value == "-1") {
        readable_value = "All tasks";
    }
    $("#pagination_current_value").prepend(readable_value);
}

//Reload current page with new pagination
function updatePagination(page_size) {
    //show the first page
    var page_number = 0;

    var url = clearUrl(window.location.href);

    url += "?page_size=" + page_size + "&page_number=" + page_number;

    window.location.href = url;
}
function setPaginationLinks(page_count, page_number, page_size) {
    var url = clearUrl(window.location.href);

    $(".fist-page-link").attr("href", url + "?page_size=" + page_size + "&page_number=0");

    //generate buttons 3 to the left and 3 to the right of current page_number
    var link_template = "<li><a href='$url' id='$id'>$text</a></li>";
    for (var i = Math.max(0, page_number - 3); i <= Math.min(Math.max(0, page_count - 1), page_number + 3); i++) {
        $(".last-page-link").parent("li").before(link_template
                                                     .replace("$url", url + "?page_size=" + page_size + "&page_number=" + i)
                                                     .replace("$text", (i + 1).toString())
                                                     .replace("$id", "page-link-" + i));
    }
    var current_button = $("#page-link-" + page_number).parent("li");
    current_button.addClass("disabled");
    current_button.addClass("active");

    $(".last-page-link").attr("href", url + "?page_size=" + page_size + "&page_number=" + Math.max(0, page_count - 1));
}

function bindPaginationDropdownHandlers() {
    $("#page-size li a").click(function () {
        $this = $(this);
        selected_size = $this.attr("data-value");
        updatePagination(selected_size);
    })
}

function clearUrl(url) {
   if (url.indexOf("?") != -1) {
        url = url.split("?")[0]
   }
   return url;
}
