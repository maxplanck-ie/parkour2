Ext.define('MainHub.store.libraries.IndexI5', {
    extend: 'Ext.data.Store',
    storeId: 'indexI5Store',

    requires: [
        'MainHub.model.libraries.Index'
    ],

    model: 'MainHub.model.libraries.Index',

    proxy: {
        type: 'ajax',
        url: 'api/indices/i5/',
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
