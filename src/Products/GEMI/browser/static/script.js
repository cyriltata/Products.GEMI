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
            var $iframe = $('#content-core-iframe');
            if (!$iframe.length) {
                return;
            }

            $iframe.bind('load', function() {
                var contents = $iframe.contents().find('#content-core').html();
                $('#content-core').html(contents);
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



