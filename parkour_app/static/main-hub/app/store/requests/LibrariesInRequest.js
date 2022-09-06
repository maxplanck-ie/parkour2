Ext.define('MainHub.store.requests.LibrariesInRequest', {
    extend: 'Ext.data.Store',
    storeId: 'librariesInRequestStore',

    requires: [
        'MainHub.model.Record'
    ],

    model: 'MainHub.model.Record',

    proxy: {
        type: 'ajax',
        // timeout: 1000000,
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
