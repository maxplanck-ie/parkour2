Ext.define('MainHub.store.libraries.IndexI7', {
    extend: 'Ext.data.Store',
    storeId: 'indexI7Store',

    requires: [
        'MainHub.model.libraries.Index'
    ],

    model: 'MainHub.model.libraries.Index',

    proxy: {
        type: 'ajax',
        url: 'api/indices/i7/',
        timeout: 1000000,
        pageParam: false,   //to remove param "page"
        startParam: false,  //to remove param "start"
        limitParam: false,  //to remove param "limit"
        noCache: false,     //to remove param "_dc",
        reader: {
            type: 'json',
            rootProperty: 'data',
            successProperty: 'success'
        }
    }
});
