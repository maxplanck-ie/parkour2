Ext.define('MainHub.store.libraries.RNAQuality', {
    extend: 'Ext.data.Store',
    storeId: 'rnaQualityStore',

    requires: [
        'MainHub.model.libraries.RNAQuality'
    ],

    model: 'MainHub.model.libraries.RNAQuality',

    data: [
        { value: 1, name: '1' },
        { value: 2, name: '2' },
        { value: 3, name: '3' },
        { value: 4, name: '4' },
        { value: 5, name: '5' },
        { value: 6, name: '6' },
        { value: 7, name: '7' },
        { value: 8, name: '8' },
        { value: 9, name: '9' },
        { value: 10, name: '10' },
        { value: 11, name: 'Determined by Facility' }
    ]
});
