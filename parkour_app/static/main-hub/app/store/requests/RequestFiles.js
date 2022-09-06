Ext.define('MainHub.store.requests.RequestFiles', {
    extend: 'Ext.data.Store',
    storeId: 'requestFilesStore',

    requires: [
        'MainHub.model.requests.RequestFile'
    ],

    model: 'MainHub.model.requests.RequestFile',

    proxy: {
        type: 'ajax',
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
