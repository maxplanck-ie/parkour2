Ext.define('MainHub.store.requests.PrincipalInvestigators', {
  extend: 'Ext.data.Store',
  storeId: 'PrincipalInvestigators',

  requires: [
    'MainHub.model.requests.PrincipalInvestigator'
  ],

  model: 'MainHub.model.requests.PrincipalInvestigator',

  proxy: {
    url: 'api/principal_investigators/',
    type: 'ajax',
    timeout: 1000000,
    pageParam: false,  // to remove param "page"
    startParam: false, // to remove param "start"
    limitParam: false, // to remove param "limit"
    noCache: false     // to remove param "_dc"
  }
});
