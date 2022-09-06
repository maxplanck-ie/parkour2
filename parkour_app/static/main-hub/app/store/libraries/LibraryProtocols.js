Ext.define('MainHub.store.libraries.LibraryProtocols', {
    extend: 'Ext.data.Store',
    storeId: 'libraryProtocolsStore',

    requires: [
        'MainHub.model.libraries.LibraryProtocol'
    ],

    model: 'MainHub.model.libraries.LibraryProtocol',

    proxy: {
        type: 'ajax',
        url: 'api/library_protocols/',
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
    },

    autoLoad: true
});
