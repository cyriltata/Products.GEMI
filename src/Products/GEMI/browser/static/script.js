/**
 * Product.GEMI javascript
 */

(function ($) {

    function parseUrl(url) {
        var parser = document.createElement('a');
        parser.href = url;
        return parser;
    }

    function scrollTo(selector) {
        $('html, body').animate({
            scrollTop: $(selector).offset().top
        }, 500);
    }

    var app = {

        init: function () {
            console.log("ProductsGEMI plugin initialized");
            app.initViews();
            app.initTabs();
        },

        initViews: function () {
            app.embedContentView()
        },

        embedContentView: function () {
            if (!$('body').is('.template-view_with_slugs')) {
                return;
            }

            var $navigation = $('#content-core .listingBar');
            $navigation.find('a').unbind('click').bind('click', function (e) {
                e.preventDefault();
                var $this = $(this);
                var href = $this.attr('href');
                var context = $this.parents('.products-gemi-embed').data('context')
                var parent_id = $this.parents('.products-gemi-embed').attr('id');
                if (!context || !href) {
                    return false;
                }

                var parse_href = parseUrl(href);
                var fetch_url = context + '/' + parse_href.search;

                $.get(fetch_url, function (data) {
                    scrollTo('#' + parent_id);
                    var content_core = $(data).find('#content-core').html();
                    $('#' + parent_id).html(content_core)
                    app.initViews();
                });
                return false;
            });
        },
 
        initTabs: function() {
            if (!$('.has-tabs').length) {
                return;
            }
            $('.has-tabs').each(function(i, e) {
                var $container = $(e);
                $container.find('ul.tab-tabs>li>a').bind('click', function(){
                    $container.find('ul.tab-tabs>li').removeClass('active');
                    $container.find('.tab-content').removeClass('active');
                    var $this = $(this);
                    $this.parents('li').addClass('active');
                    $container.find($this.data('href')).addClass('active');
                });
            });
        }
    };

    $(document).ready(app.init);
})(jQuery);



