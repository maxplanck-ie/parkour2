Ext.define('MainHub.model.pooling.Pooling', {
    extend: 'MainHub.model.Record',

    fields: [
        {
            name: 'request',
            type: 'int'
        },
        {
            name: 'request_name',
            type: 'string'
        },
        {
            name: 'pool',
            type: 'int'
        },
        {
            name: 'pool_name',
            type: 'string'
        },
        {
            name: 'create_time',
            type: 'date'
        },
        {
            name: 'pool_size',
            type: 'string'
        },
        {
            name: 'concentration_library',
            type: 'float',
            allowNull: true
        },
        {
            name: 'mean_fragment_size',
            type: 'int',
            allowNull: true
        },
        {
            name: 'concentration_c1',
            type: 'float',
            allowNull: true
        },
        {
            name: 'sequencing_depth',
            type: 'float'
        },
        {
            name: 'percentage_library',
            type: 'string'
        },
        {
            name: 'coordinate',
            type: 'string'
        },
        {
            name: 'index_i7_id',
            type: 'string'
        },
        {
            name: 'index_i5_id',
            type: 'string'
        },
        {
            name: 'index_i7',
            type: 'string'
        },
        {
            name: 'index_i5',
            type: 'string'
        },
        {
            name: 'quality_check',
            type: 'string',
            allowNull: true
        },
        {
            name: 'comment',
            type: 'string'
        }
    ]
});
