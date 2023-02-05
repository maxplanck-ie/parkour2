from django.contrib.auth.models import Permission

_group_permissions_codenames = ['view_group',

                                'add_costunit',
                                'change_costunit',
                                'view_costunit',

                                'add_oidcgroup',
                                'change_oidcgroup',
                                'delete_oidcgroup',
                                'view_oidcgroup',

                                'add_organization',
                                'change_organization',
                                'view_organization',

                                'add_principalinvestigator',
                                'change_principalinvestigator',
                                'view_principalinvestigator',

                                'add_user',
                                'change_user',
                                'view_user',

                                'add_flowcell',
                                'change_flowcell',
                                'view_flowcell',

                                'add_lane',
                                'change_lane',
                                'view_lane',

                                'add_sequencer',
                                'change_sequencer',
                                'view_sequencer',

                                'add_pool',
                                'change_pool',
                                'view_pool',

                                'add_poolsize',
                                'change_poolsize',
                                'view_poolsize',

                                'add_fixedcosts',
                                'change_fixedcosts',
                                'view_fixedcosts',

                                'add_fixedprice',
                                'change_fixedprice',
                                'delete_fixedprice',
                                'view_fixedprice',

                                'add_invoicingreport',
                                'change_invoicingreport',
                                'view_invoicingreport',

                                'add_librarypreparationcosts',
                                'change_librarypreparationcosts',
                                'view_librarypreparationcosts',

                                'add_librarypreparationprice',
                                'change_librarypreparationprice',
                                'delete_librarypreparationprice',
                                'view_librarypreparationprice',

                                'add_sequencingcosts',
                                'change_sequencingcosts',
                                'view_sequencingcosts',

                                'add_sequencingprice',
                                'change_sequencingprice',
                                'delete_sequencingprice',
                                'view_sequencingprice',

                                'add_library',
                                'change_library',
                                'view_library',

                                'add_librarypreparation',
                                'change_librarypreparation',
                                'view_librarypreparation',

                                'add_barcodecounter',
                                'change_barcodecounter',
                                'view_barcodecounter',

                                'add_concentrationmethod',
                                'change_concentrationmethod',
                                'view_concentrationmethod',

                                'add_indexi5',
                                'change_indexi5',
                                'view_indexi5',

                                'add_indexi7',
                                'change_indexi7',
                                'view_indexi7',

                                'add_indexpair',
                                'change_indexpair',
                                'view_indexpair',

                                'add_indextype',
                                'change_indextype',
                                'view_indextype',

                                'add_libraryprotocol',
                                'change_libraryprotocol',
                                'view_libraryprotocol',

                                'add_librarytype',
                                'change_librarytype',
                                'view_librarytype',

                                'add_organism',
                                'change_organism',
                                'view_organism',

                                'add_readlength',
                                'change_readlength',
                                'view_readlength',

                                'add_pooling',
                                'change_pooling',
                                'view_pooling',

                                'add_filerequest',
                                'change_filerequest',
                                'view_filerequest',

                                'add_request',
                                'change_request',
                                'view_request',

                                'add_nucleicacidtype',
                                'change_nucleicacidtype',
                                'view_nucleicacidtype',

                                'add_sample',
                                'change_sample',
                                'view_sample']

GROUP_PERMISSIONS = Permission.objects.filter(
    codename__in=_group_permissions_codenames)
