/* Functions for the embed content plugin popup */
/*jslint evil: true */
/*global jq, tinymce, tinyMCEPopup, alert */
// tinyMCEPopup.requireLangPack();



function str_template_replace(str, params) {
    for (var i in params) {
        var re = new RegExp('{'+i+'}', 'g');
        str = str.replace(re, params[i]);
    }
    return str;
}

var _selfECBD;

/**
 * Content selection dialog.
 *
 * @param mcePopup Reference to a corresponding TinyMCE popup object.
 */
var EmbedContentBrowserDialog = function (mcePopup) {
    _selfECBD = this;

    this.tinyMCEPopup = mcePopup;
    this.editor = mcePopup.editor;
    this.isAjaxing = false;
    this.params = this.tinyMCEPopup.params;
    this.fetch_url = this.params.plugin_url + "/../@@embedcontent-plugin.html";
    this.templates = {
        "crumb": '<a href="#" data-context="{context}" data-isf="{isf}" data-url="{url}">{title}</a>',
        "item": '<li><label class="label summary"><input type="radio" name="content" value="{context}"><span data-url="{url}" class="{klass}" data-context="{context}" data-isf="{isf}">{title}</span></label></li>'
    };
};

EmbedContentBrowserDialog.prototype.init = function() {
    this.listing = document.getElementById('content-items-listing');
    this.crumbs = document.getElementById('content-breadcrumbs');
    this.listing.addEventListener("dblclick", this.dblClick);
    this.crumbs.addEventListener("click", this.click);
    if (this.params.context) {
        this.getListing(this.params.context, 0);
    } else {
        jq(this.listing).show();
    }
    
}

EmbedContentBrowserDialog.prototype.getListing = function(context, path_is_parent) {
    var _self = this;
    jq.ajax({
        url: this.fetch_url,
        data: {is_ajax: 1, path: context, pip: path_is_parent},
        success: function(data) {
            if (data && data.contents.length) {
                var content_html = '';
                for (var i in data.contents) {
                    content_html += str_template_replace(_self.templates.item, data.contents[i]);
                }
                
                var breadcrumb_html = '';
                for (var i in data.crumbs) {
                    breadcrumb_html += str_template_replace(_self.templates.crumb, data.crumbs[i]) + ' &raquo; ';
                }

                _self.listing.innerHTML = content_html;
                _self.crumbs.innerHTML = breadcrumb_html;
                
                jq(_self.listing).show();
                // check something if it was set
                if (_self.params.context) {
                     jq(_self.listing).find('input[value="'+_self.params.context+'"]').attr('checked', 'checked');
                }
            }
        },
        dataType: 'json'
    });
}

EmbedContentBrowserDialog.prototype.click = function(event) {
    event.preventDefault();
    _selfECBD.dblClick(event);
}

EmbedContentBrowserDialog.prototype.dblClick = function(event) {
    event.preventDefault();
    var $target = jq(event.target);
    var data = $target.data();
    if (data && data.context) {
         _selfECBD.getListing(data.context, 1);
    }
}

EmbedContentBrowserDialog.prototype.insert = function() {
    var $listing = jq(this.listing);
    var path = null;
    $listing.find('label input[name=content]').each(function() {
        if (jq(this).is(':checked')) {
            path = jq(this).val(); 
        }
    });

    if (!path) {
        // maybe show error to select something
        return false;
    }

    var html = "<div class='plone-emebeded-content'>{{{external_content="+path+"}}}</div>";
    html += '<p></p>';
    if (this.params.context) {
        var node = this.editor.selection.getNode();
        //@todo check node
        node.remove();
    }

    this.editor.execCommand('mceInsertContent', false, html);
    this.tinyMCEPopup.close();
    
}

var ecBrowserDialog = new EmbedContentBrowserDialog(tinyMCEPopup);
tinyMCEPopup.onInit.add(ecBrowserDialog.init, ecBrowserDialog);
