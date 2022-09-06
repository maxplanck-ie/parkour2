Ext.define('MainHub.store.libraries.Libraries', {
    extend: 'Ext.data.TreeStore',
    storeId: 'librariesStore',

    requires: [
        'MainHub.model.libraries.Library'
    ],

    model: 'MainHub.model.libraries.Library',

    proxy: {
        type: 'ajax',
        url: '/api/libraries_and_samples/',
        noCache: false,     //to remove param "_dc",
        reader: 'json',
        extraParams:{
        showAll: 'True'
    }
    },

    lazyFill: true
});
