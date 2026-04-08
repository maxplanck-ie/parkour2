Ext.define('MainHub.view.indexgeneratorvue.IndexGeneratorVue', {
    extend: 'Ext.panel.Panel',
    xtype: 'index-generator-vue',

    config: {
        header: false,
        layout: 'fit',
        listeners: {
            afterrender: function () {
                var iframe = document.createElement('iframe');
                iframe.src = '/vue/indexgenerator';
                iframe.style.width = '100%';
                iframe.style.height = '100%';
                iframe.style.border = 'none';
                this.body.dom.appendChild(iframe);
            }
        }
    }
});
