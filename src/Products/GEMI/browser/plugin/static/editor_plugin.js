(function () {
    if (!window.tinymce) {
        return;
    }

    var current_context = null;
    
    var loadCssInterval = null;

    // Create plugin
    tinymce.create('tinymce.plugins.EmbedContentPlugin', {

        init: function (ed, url) {
            // Register css
            try {
                loadCssInterval = setInterval(function(){
                    if (tinymce.get(ed.id).dom) {
                        tinymce.get(ed.id).dom.loadCSS(url + '/editor_plugin.css');
                        clearInterval(loadCssInterval)
                    }
                }, 1000);
            } catch (e) {
                console.log(e)
            }

            // Register the command so that it can be invoked by using tinyMCE.activeEditor.execCommand('mceExample');
            ed.addCommand('embedcontent', function (e) {
                try {
                    // Open add tile menu
                    ed.windowManager.open({
                        file: url + "/../@@embedcontent-plugin.html",
                        width: 820,
                        height: 480,
                        inline: 1
                    }, {
                        plugin_url: url,
                        context: current_context
                    });
                } catch (e) {
                    console.log('Whoops. Something went wrong! Content can\'t be embeded');
                }
            });
            
            ed.onClick.add(function(i, e) {
                var $target = $(e.target);
                if ($target.is('.plone-emebeded-content')) {
                    var regex = '{{{external_content=(.*?)}}}';
                    var re = new RegExp(regex, "g");
                    var matches = re.exec($target.text())
                    if (matches && typeof matches[1] !== 'undefined') {
                        current_context = matches[1];
                        tinymce.activeEditor.controlManager.setActive('embedcontent', true);
                        return;
                    }
                }

                tinymce.activeEditor.controlManager.setActive('embedcontent', false);
                current_context = null
            });

            // Register example button
            ed.addButton('embedcontent', {
                title: 'Embed Content',
                cmd: 'embedcontent',
                image: url + '/embedcontent.gif'
            });
        },

        getInfo: function () {
            return {
                longname: 'Embed Content Plugin',
                author: 'Cyril Tata',
                authorurl: 'http://cyriltata.blogspot.com',
                infourl: 'http://plone.org/products/tinymce',
                version: tinymce.majorVersion + "." + tinymce.minorVersion
            };
        }
    });
    
    // Register plugin
    tinymce.PluginManager.add('embedcontent', tinymce.plugins.EmbedContentPlugin);
})();