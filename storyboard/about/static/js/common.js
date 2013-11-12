var page_type;

function prepareAJAX() {
    var csrftoken = $.cookie('csrftoken');
    $.ajaxSetup({
        crossDomain: false,
        beforeSend: function(xhr, settings) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    });
}

function setPageType(type) {
    page_type = type;
}