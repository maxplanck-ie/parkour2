Ext.define('MainHub.model.libraries.ConcentrationMethod', {
    extend: 'MainHub.model.Base',

    fields: [
        {name: 'name', type: 'string'},
        {name: 'id', type: 'int'}
    ],

    getShortName: function() {
        var name = this.get('name');
        var abbr = name.split(' ').map(function(item) {
            return item.charAt(0);
        });
        return abbr.join('');
    }
});
