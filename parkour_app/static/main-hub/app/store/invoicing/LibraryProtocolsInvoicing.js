Ext.define('MainHub.store.invoicing.LibraryProtocolsInvoicing', {
    extend: 'Ext.data.Store',
    storeId: 'libraryprotocolinvoicingStore',

    requires: [
        'MainHub.model.libraries.LibraryProtocol'
    ],

    model: 'MainHub.model.libraries.LibraryProtocol',

    proxy: {
        type: 'ajax',
        url: 'api/library_protocols_invoicing/',
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
