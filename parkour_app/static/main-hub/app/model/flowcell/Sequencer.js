Ext.define('MainHub.model.flowcell.Sequencer', {
    extend: 'MainHub.model.Base',

    fields: [{
        name: 'name',
        type: 'string'
    }, {
        name: 'id',
        type: 'int'
    }, {
        name: 'lanes',
        type: 'int'
    }, {
        name: 'lane_capacity',
        type: 'int'
    }]
});
