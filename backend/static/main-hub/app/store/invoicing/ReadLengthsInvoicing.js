Ext.define('MainHub.store.invoicing.ReadLengthsInvoicing', {
    extend: 'Ext.data.Store',
    storeId: 'readLengthsInvoicingStore',

    requires: [
        'MainHub.model.libraries.ReadLength'
    ],

    model: 'MainHub.model.libraries.ReadLength',

    proxy: {
        type: 'ajax',
        url: 'api/read_lengths_invoicing/',
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
