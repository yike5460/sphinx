Search.setIndex({docnames:["api","api.adapter","api.adapter.em","api.adapter.mano","api.adapter.traffic","api.adapter.vim","api.adapter.vnf","api.adapter.vnfm","api.generic","api.structures","index","modules","source/api","source/api.adapter","source/api.adapter.em","source/api.adapter.mano","source/api.adapter.traffic","source/api.adapter.vim","source/api.adapter.vnf","source/api.adapter.vnfm","source/api.generic","source/api.structures","source/modules"],envversion:52,filenames:["api.rst","api.adapter.rst","api.adapter.em.rst","api.adapter.mano.rst","api.adapter.traffic.rst","api.adapter.vim.rst","api.adapter.vnf.rst","api.adapter.vnfm.rst","api.generic.rst","api.structures.rst","index.rst","modules.rst","source/api.rst","source/api.adapter.rst","source/api.adapter.em.rst","source/api.adapter.mano.rst","source/api.adapter.traffic.rst","source/api.adapter.vim.rst","source/api.adapter.vnf.rst","source/api.adapter.vnfm.rst","source/api.generic.rst","source/api.structures.rst","source/modules.rst"],objects:{"":{api:[0,0,0,"-"]},"api.adapter":{ApiAdapterError:[1,1,1,""],construct_adapter:[1,2,1,""],em:[14,0,0,"-"],mano:[15,0,0,"-"],traffic:[16,0,0,"-"],vim:[17,0,0,"-"],vnf:[6,0,0,"-"],vnfm:[19,0,0,"-"]},"api.adapter.em":{EmAdapterError:[14,1,1,""]},"api.adapter.mano":{ManoAdapterError:[15,1,1,""]},"api.adapter.traffic":{TrafficAdapterError:[16,1,1,""],ping:[16,0,0,"-"]},"api.adapter.traffic.ping":{PingTrafficAdapter:[16,3,1,""],PingTrafficAdapterError:[16,1,1,""]},"api.adapter.traffic.ping.PingTrafficAdapter":{any_traffic_loss:[16,4,1,""],clear_counters:[16,4,1,""],configure:[16,4,1,""],destroy:[16,4,1,""],does_traffic_flow:[16,4,1,""],reconfig_traffic_dest:[16,4,1,""],start:[16,4,1,""],stop:[16,4,1,""]},"api.adapter.vim":{VimAdapterError:[17,1,1,""]},"api.adapter.vnf":{VnfAdapterError:[6,1,1,""],cirros:[6,0,0,"-"],dummy:[6,0,0,"-"],openwrt:[6,0,0,"-"],ubuntu:[6,0,0,"-"]},"api.adapter.vnf.cirros":{CirrosVnfAdapter:[6,3,1,""],CirrosVnfAdapterError:[6,1,1,""]},"api.adapter.vnf.cirros.CirrosVnfAdapter":{config_applied:[6,4,1,""],license_applied:[6,4,1,""]},"api.adapter.vnf.dummy":{DummyVnfAdapter:[6,3,1,""],DummyVnfAdapterError:[6,1,1,""]},"api.adapter.vnf.dummy.DummyVnfAdapter":{get_operation_status:[6,4,1,""],scale_to_level:[6,4,1,""]},"api.adapter.vnf.openwrt":{OpenwrtVnfAdapter:[6,3,1,""],OpenwrtVnfAdapterError:[6,1,1,""]},"api.adapter.vnf.openwrt.OpenwrtVnfAdapter":{config_applied:[6,4,1,""],license_applied:[6,4,1,""],scale:[6,4,1,""]},"api.adapter.vnf.ubuntu":{UbuntuVnfAdapter:[6,3,1,""],UbuntuVnfAdapterError:[6,1,1,""]},"api.adapter.vnf.ubuntu.UbuntuVnfAdapter":{config_applied:[6,4,1,""],license_applied:[6,4,1,""]},"api.adapter.vnfm":{VnfmAdapterError:[19,1,1,""]},"api.generic":{ApiGenericError:[20,1,1,""],constants:[20,0,0,"-"],construct_generic:[20,2,1,""],em:[20,0,0,"-"],mano:[20,0,0,"-"],traffic:[20,0,0,"-"],vnf:[20,0,0,"-"]},"api.generic.em":{Em:[20,3,1,""],EmGenericError:[20,1,1,""]},"api.generic.em.Em":{get_operation_status:[20,4,1,""],modify_vnf_configuration:[20,4,1,""],poll_for_operation_completion:[20,4,1,""],set_generic_config:[20,4,1,""],vnf_scale:[20,4,1,""],vnf_scale_sync:[20,4,1,""]},"api.generic.mano":{Mano:[20,3,1,""],ManoGenericError:[20,1,1,""]},"api.generic.mano.Mano":{get_allocated_vresources:[20,4,1,""],get_notification_queue:[20,4,1,""],get_ns_ingress_cp_addr_list:[20,4,1,""],get_nsd_scaling_properties:[20,4,1,""],get_operation_status:[20,4,1,""],get_vim_helper:[20,4,1,""],get_vnf_ingress_cp_addr_list:[20,4,1,""],get_vnf_instance_id_from_ns_vnf_name:[20,4,1,""],get_vnf_mgmt_addr_list:[20,4,1,""],get_vnfd_name_from_nsd_vnf_name:[20,4,1,""],get_vnfd_scaling_properties:[20,4,1,""],limit_compute_resources_for_ns_scaling:[20,4,1,""],limit_compute_resources_for_vnf_instantiation:[20,4,1,""],limit_compute_resources_for_vnf_scaling:[20,4,1,""],limit_storage_resources_for_vnf_instantiation:[20,4,1,""],modify_vnf_configuration:[20,4,1,""],ns_create_and_instantiate:[20,4,1,""],ns_create_id:[20,4,1,""],ns_delete_id:[20,4,1,""],ns_get_alarm_list:[20,4,1,""],ns_instantiate:[20,4,1,""],ns_instantiate_sync:[20,4,1,""],ns_lifecycle_change_notification_subscribe:[20,4,1,""],ns_query:[20,4,1,""],ns_scale:[20,4,1,""],ns_scale_sync:[20,4,1,""],ns_terminate:[20,4,1,""],ns_terminate_and_delete:[20,4,1,""],ns_terminate_sync:[20,4,1,""],ns_update:[20,4,1,""],ns_update_sync:[20,4,1,""],nsd_delete:[20,4,1,""],nsd_fetch:[20,4,1,""],nsd_info_create:[20,4,1,""],nsd_info_query:[20,4,1,""],nsd_upload:[20,4,1,""],poll_for_operation_completion:[20,4,1,""],resolve_ns_cp_addr:[20,4,1,""],search_in_notification_queue:[20,4,1,""],set_generic_config:[20,4,1,""],validate_ns_allocated_vresources:[20,4,1,""],validate_ns_instantiation_level:[20,4,1,""],validate_ns_released_vresources:[20,4,1,""],validate_vnf_allocated_vresources:[20,4,1,""],validate_vnf_deployment_flavour:[20,4,1,""],validate_vnf_instantiation_level:[20,4,1,""],validate_vnf_released_vresources:[20,4,1,""],validate_vnf_vresource_state:[20,4,1,""],verify_ns_sw_images:[20,4,1,""],verify_ns_vnf_instance_count:[20,4,1,""],verify_vnf_nsd_mapping:[20,4,1,""],verify_vnf_sw_images:[20,4,1,""],vnf_change_flavour:[20,4,1,""],vnf_create_and_instantiate:[20,4,1,""],vnf_create_id:[20,4,1,""],vnf_delete_id:[20,4,1,""],vnf_instantiate:[20,4,1,""],vnf_instantiate_sync:[20,4,1,""],vnf_lifecycle_change_notification_subscribe:[20,4,1,""],vnf_operate:[20,4,1,""],vnf_operate_sync:[20,4,1,""],vnf_query:[20,4,1,""],vnf_scale:[20,4,1,""],vnf_scale_sync:[20,4,1,""],vnf_scale_to_level:[20,4,1,""],vnf_scale_to_level_sync:[20,4,1,""],vnf_terminate:[20,4,1,""],vnf_terminate_and_delete:[20,4,1,""],vnf_terminate_sync:[20,4,1,""],wait_for_notification:[20,4,1,""],wait_for_ns_stable_state:[20,4,1,""],wait_for_vnf_stable_state:[20,4,1,""]},"api.generic.traffic":{Traffic:[20,3,1,""],TrafficGenericError:[20,1,1,""]},"api.generic.traffic.Traffic":{any_traffic_loss:[20,4,1,""],calculate_activation_time:[20,4,1,""],calculate_deactivation_time:[20,4,1,""],calculate_service_disruption_length:[20,4,1,""],clear_counters:[20,4,1,""],config_traffic_load:[20,4,1,""],configure:[20,4,1,""],destroy:[20,4,1,""],does_traffic_flow:[20,4,1,""],reconfig_traffic_dest:[20,4,1,""],start:[20,4,1,""],stop:[20,4,1,""]},"api.generic.vnf":{Vnf:[20,3,1,""],VnfGenericError:[20,1,1,""]},"api.generic.vnf.Vnf":{config_applied:[20,4,1,""],get_operation_status:[20,4,1,""],license_applied:[20,4,1,""],poll_for_operation_completion:[20,4,1,""],scale:[20,4,1,""],scale_sync:[20,4,1,""]},api:{ApiError:[0,1,1,""],adapter:[1,0,0,"-"],generic:[20,0,0,"-"],structures:[21,0,0,"-"]}},objnames:{"0":["py","module","Python module"],"1":["py","exception","Python exception"],"2":["py","function","Python function"],"3":["py","class","Python class"],"4":["py","method","Python method"]},objtypes:{"0":"py:module","1":"py:exception","2":"py:function","3":"py:class","4":"py:method"},terms:{"boolean":[8,20],"case":[8,20],"class":[4,6,8,16,18,20],"default":[8,20],"final":[8,20],"function":[1,6,8,13,18,20],"new":[8,20],"return":[1,8,13,20],"true":[8,20],Adding:[8,20],For:[8,20],The:[1,8,13,20],VLs:[8,20],about:[8,20],absent:[8,20],accept:[8,20],accord:[8,20],action:[8,20],activ:[8,20],actual:[8,20],adapt:[0,8,10,11,12,20,22],adapter_config:[8,20],add_nested_ns_id:[8,20],add_sap:[8,20],add_vnf_inst:[8,20],add_vnffg:[8,20],added:[8,20],adding:[8,20],addit:[1,8,13,20],additional_affinity_or_anti_affinity_rul:[8,20],additional_param:[8,20],additional_param_for_n:[8,20],additional_param_for_vnf:[8,20],addnestedn:[8,20],addr_typ:[8,20],address:[8,20],addsap:[8,20],addvnf:[8,20],addvnffg:[8,20],affect:[8,20],affin:[8,20],alarm:[8,20],alarmid:[8,20],all:[8,20],alloc:[8,20],allow:[8,20],alreadi:[8,20],also:[8,20],ani:[8,20],annex:[8,20],anoth:[8,20],anti:[8,20],any_traffic_loss:[4,8,16,20],api:10,apiadaptererror:[1,2,3,4,5,6,7,13,14,15,16,17,18,19],apierror:[0,1,8,12,13,20],apigenericerror:[8,20],appli:[8,20],applic:[8,20],approach:[8,20],arg:[4,16],aspect:[8,20],aspect_id:[8,20],assoc_new_nsd_version_data:[8,20],associ:[8,20],assocnewnsdvers:[8,20],attribut:[8,20],attribute_selector:[8,20],attributeselector:[8,20],automat:[8,20],back:[8,20],base:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],been:[8,20],befor:[8,20],being:[8,20],belong:[8,20],between:[8,20],both:[8,20],bottom:[8,20],bss:[8,20],bsss:[8,20],calculate_activation_tim:[8,20],calculate_deactivation_tim:[8,20],calculate_service_disruption_length:[8,20],can:[8,20],cardin:[8,20],caus:[8,20],chang:[8,20],change_ext_vnf_connectivity_data:[8,20],change_ns_flavour_data:[8,20],change_state_to:[8,20],change_vnf_flavour_data:[8,20],changeextvnfconnect:[8,20],changensdf:[8,20],changevnfdf:[8,20],check:[8,20],chosen:[8,20],cirro:[0,1,10,12,13],cirrosvnfadapt:[6,18],cirrosvnfadaptererror:[6,18],cisconfv45:[0,1,10,12,13],cisconfv:[0,1,10,12,13],clear:[8,20],clear_count:[4,8,16,20],command:[8,20],commun:[8,20],compar:[8,20],complet:[8,20],complex:[],comput:[8,20],concern:[8,20],config_appli:[6,8,18,20],config_traffic_load:[8,20],configur:[4,8,16,20],connect:[8,20],consecut:[8,20],consid:[8,20],constant:[0,10,11,12,22],constraint:[8,20],construct_adapt:[1,13],construct_gener:[8,20],constructor:[1,8,13,20],contain:[8,20],content:[10,11,22],control:[8,20],correct:[8,20],correspond:[8,20],could:[8,20],counter:[8,20],cp1:[8,20],cp2:[8,20],cp_name:[8,20],creat:[8,20],creation:[8,20],criteria:[8,20],current:[8,20],data:[8,20],declar:[8,20],defin:[8,20],definit:[8,20],delay_tim:[4,8,16,20],delet:[8,20],deploi:[8,20],deploy:[8,20],descript:[8,20],desir:[8,20],desired_scale_out_step:[8,20],dest_addr_list:[4,16],destin:[8,20],destroi:[4,8,16,20],detail:[8,20],detect:[8,20],determin:[8,20],dictionari:[8,20],direct:[8,20],does_traffic_flow:[4,8,16,20],doing:[8,20],down:[8,20],drop:[8,20],dummi:[0,1,10,12,13],dummyvnfadapt:[6,18],dummyvnfadaptererror:[6,18],dure:[8,20],each:[8,20],earliest:[8,20],east:[8,20],either:[8,20],element:[8,20],emadaptererror:[2,14],emb:[8,20],emgenericerror:[8,20],emiss:[8,20],empirix:[8,20],enabl:[8,20],end:[8,20],enough:[8,20],entiti:[8,20],etsi:[8,20],exampl:[8,20],except:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],execut:[8,20],exist:[8,20],expect:[8,20],expected_flavour_id:[8,20],expected_instantiation_level_id:[8,20],explan:[8,20],expos:[6,8,18,20],exposur:[8,20],ext_managed_virtual_link:[8,20],ext_virtual_link:[8,20],extern:[8,20],fail:[8,20],fals:[8,20],faultdetail:[8,20],fetch:[1,8,13,20],filter:[8,20],final_st:[8,20],fine:[8,20],flag:[8,20],flavor:[8,20],flavour:[8,20],flavour_id:[8,20],flow:[8,20],follow:[8,20],forc:[8,20],format:[8,20],found:[8,20],from:[8,20],from_level:[],gener:[0,10,11,12,22],generic_config:[8,20],generic_vim_object:[8,20],get:[8,20],get_allocated_vresourc:[8,20],get_notification_queu:[8,20],get_ns_ingress_cp_addr_list:[8,20],get_nsd_scaling_properti:[8,20],get_operation_statu:[6,8,18,20],get_vim_help:[8,20],get_vnf_ingress_cp_addr_list:[8,20],get_vnf_instance_id_from_ns_vnf_nam:[8,20],get_vnf_mgmt_addr_list:[8,20],get_vnfd_name_from_nsd_vnf_nam:[8,20],get_vnfd_scaling_properti:[8,20],given:[8,20],goe:[8,20],grace:[8,20],graceful_stop_timeout:[8,20],graceful_termination_timeout:[8,20],grain:[8,20],has:[8,20],have:[8,20],hold:[8,20],horizont:[8,20],human:[8,20],identifi:[8,20],ifa:[8,20],imag:[8,20],immedi:[8,20],includ:[8,20],index:10,indic:[8,20],influenc:[8,20],inform:[8,20],ingress:[8,20],ingress_cp_list:[8,20],initi:[8,20],input:[8,20],insid:[8,20],inst:[],instanc:[8,20],instanti:[8,20],instantiate_vnf_data:[8,20],instantiatevnf:[8,20],instantiation_level_id:[8,20],instantiation_level_list:[8,20],instantiationlevelid:[8,20],interfac:[8,20],intern:[8,20],interv:[8,20],item:[8,20],its:[8,20],just:[8,20],kei:[1,8,13,20],known:[8,20],kwarg:[1,4,6,8,13,16,18,20],languag:[8,20],lcm:[8,20],level:[8,20],licens:[8,20],license_appli:[6,8,18,20],lifecycl:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],lifecycle_operation_occurrence_id:[8,20],like:[8,20],limit:[8,20],limit_compute_resources_for_ns_sc:[8,20],limit_compute_resources_for_vnf_instanti:[8,20],limit_compute_resources_for_vnf_sc:[8,20],limit_storage_resources_for_vnf_instanti:[8,20],limit_vc_inst:[8,20],limit_vcpu:[8,20],limit_vmem:[8,20],link:[8,20],list:[8,20],load:[8,20],local:[8,20],localization_languag:[8,20],locat:[8,20],location_constraint:[8,20],logging_modul:[],lost:[8,20],low_traffic_load:[8,20],mac:[8,20],mai:[8,20],manag:[8,20],mano:[0,1,10,11,12,13,22],manoadaptererror:[3,15],manogenericerror:[8,20],map:[8,20],match:[8,20],max_traffic_load:[8,20],max_wait_tim:[8,20],maximum:[8,20],messag:[8,20],misc:[],mode:[8,20],modifi:[8,20],modify_vnf_configur:[8,20],modify_vnf_info_data:[8,20],modifyconfigur:[8,20],modifyvnfinform:[8,20],modul:[10,11,22],module_typ:[1,8,13,20],more:[8,20],move:[8,20],move_vnf_instance_data:[8,20],movevnf:[8,20],name:[1,8,13,20],necessari:[8,20],need:[8,20],neg:[8,20],nest:[8,20],nested_ns_instance_data:[8,20],net:[],network:[8,20],new_flavour_id:[8,20],nfv:[8,20],nfvo:[8,20],none:[8,20],normal_traffic_load:[8,20],not_instanti:[8,20],notif:[8,20],notification_filt:[8,20],ns_create_and_instanti:[8,20],ns_create_id:[8,20],ns_delete_id:[8,20],ns_descript:[8,20],ns_get_alarm_list:[8,20],ns_info:[8,20],ns_instance_id:[8,20],ns_instanti:[8,20],ns_instantiate_sync:[8,20],ns_instantiate_timeout:[8,20],ns_instantiation_level_id:[8,20],ns_lifecycle_change_notification_subscrib:[8,20],ns_name:[8,20],ns_queri:[8,20],ns_scale:[8,20],ns_scale_sync:[8,20],ns_scale_timeout:[8,20],ns_stable_state_timeout:[8,20],ns_termin:[8,20],ns_terminate_and_delet:[8,20],ns_terminate_sync:[8,20],ns_terminate_timeout:[8,20],ns_updat:[8,20],ns_update_sync:[8,20],ns_update_timeout:[8,20],nsd:[8,20],nsd_delet:[8,20],nsd_fetch:[8,20],nsd_id:[8,20],nsd_info_cr:[8,20],nsd_info_id:[8,20],nsd_info_queri:[8,20],nsd_upload:[8,20],nsinfo:[8,20],nss:[8,20],number:[8,20],number_of_step:[8,20],object:[0,4,6,8,10,11,12,16,18,20,22],occur:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],occurr:[8,20],offer:[8,20],onboard:[],one:[8,20],ones:[8,20],onli:[8,20],openbaton:[0,1,10,12,13],openstack:[0,1,8,10,12,13,20],openwrt:[0,1,10,12,13],openwrtvnfadapt:[6,18],openwrtvnfadaptererror:[6,18],oper:[6,8,18,20],operate_vnf_data:[8,20],operatevnf:[8,20],option:[8,20],origin:[8,20],oss:[8,20],other:[8,20],otherwis:[8,20],out:[8,20],outcom:[8,20],over:[8,20],packag:[10,11,22],packet:[8,20],page:10,pair:[1,8,13,20],param:[8,20],paramet:[1,8,13,20],part:[8,20],particular:[8,20],pass:[8,20],pattern:[8,20],per:[8,20],percent:[8,20],percentag:[8,20],perform:[8,20],permit:[8,20],ping:[0,1,10,12,13],pingtrafficadapt:[4,16],pingtrafficadaptererror:[4,16],place:[8,20],plugtest:[],pnf:[8,20],pnf_info:[8,20],point:[8,20],polici:[8,20],poll:[8,20],poll_for_operation_complet:[8,20],poll_interv:[8,20],possibl:[8,20],present:[8,20],problem:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],process:[8,20],properti:[8,20],provid:[8,20],queri:[8,20],query_filt:[8,20],reach:[8,20],readabl:[8,20],realiz:[8,20],receiv:[8,20],reconfig_traffic_dest:[4,8,16,20],recurs:[8,20],refer:[8,20],referenc:[8,20],relat:[8,20],releas:[8,20],remain:[8,20],remov:[8,20],remove_nested_ns_id:[8,20],remove_sap_id:[8,20],remove_vnf_instance_id:[8,20],remove_vnffg_id:[8,20],removenestedn:[8,20],removesap:[8,20],removevnf:[8,20],removevnffg:[8,20],removevnfnestedn:[8,20],report:[],repres:[6,8,18,20],request:[8,20],requir:[8,20],reserv:[8,20],resolv:[8,20],resolve_ns_cp_addr:[8,20],resourc:[8,20],rest_serv:[],restrict:[8,20],result:[8,20],retriev:[8,20],return_when_emission_start:[8,20],return_when_emission_stop:[8,20],rift:[0,1,10,12,13],run:[8,20],sap:[8,20],sap_data:[8,20],scale:[6,8,18,20],scale_info:[8,20],scale_n:[8,20],scale_ns_data:[8,20],scale_sync:[8,20],scale_tim:[8,20],scale_to_level:[6,18],scale_typ:[8,20],scale_vnf:[8,20],scale_vnf_data:[8,20],scaleinfo:[8,20],scalevnf:[8,20],scaling_policy_nam:[8,20],sdl:[0,1,10,12,13],search:[8,10,20],search_in_notification_queu:[8,20],second:[8,20],section:[8,20],see:[8,20],select:[8,20],separ:[8,20],server:[],servic:[8,20],set_generic_config:[8,20],sever:[8,20],shall:[8,20],should:[8,20],shut:[8,20],signal:[8,20],size:[8,20],sourc:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],space:[8,20],specif:[8,20],specifi:[1,8,13,20],sphinxf4lcm:[],stabl:[8,20],standard:[8,20],stare:[8,20],start:[4,8,16,20],start_tim:[8,20],state:[8,20],statu:[8,20],stc:[0,1,10,12,13],step:[8,20],stop:[4,8,16,20],stop_typ:[8,20],storag:[8,20],string:[8,20],structur:[0,8,10,11,12,20,22],stub:[6,18],submodul:[0,1,10,11,12,13,22],subpackag:[10,11,22],subscrib:[8,20],subscript:[8,20],success:[8,20],successfulli:[8,20],support:[8,20],synchron:[8,20],system:[8,20],tacker:[0,1,10,12,13],take:[8,20],taken:[8,20],target:[8,20],target_instantiation_level_id:[8,20],target_vnf_nam:[8,20],tc_vnf_complex_001:[],tc_vnf_complex_002:[],tc_vnf_complex_003:[],tc_vnf_scale_out_001__mano_manu:[],tc_vnf_scale_out_001__mano_ondemand__em_ind:[],tc_vnf_scale_out_001__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_001__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_002__mano_manu:[],tc_vnf_scale_out_002__mano_ondemand__em_ind:[],tc_vnf_scale_out_002__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_002__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_003__mano_manu:[],tc_vnf_scale_out_003__mano_ondemand__em_ind:[],tc_vnf_scale_out_003__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_003__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_004__mano_manual__step_1:[],tc_vnf_scale_out_004__mano_manual__step_max:[],tc_vnf_scale_out_004__mano_ondemand__em_ind__step_1:[],tc_vnf_scale_out_004__mano_ondemand__em_ind__step_max:[],tc_vnf_scale_out_004__mano_ondemand__vim_kpi__step_1:[],tc_vnf_scale_out_004__mano_ondemand__vim_kpi__step_max:[],tc_vnf_scale_out_004__mano_ondemand__vnf_ind__step_1:[],tc_vnf_scale_out_004__mano_ondemand__vnf_ind__step_max:[],tc_vnf_scale_out_005__mano_manu:[],tc_vnf_scale_out_005__mano_ondemand__em_ind:[],tc_vnf_scale_out_005__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_005__mano_ondemand__vnf_ind:[],tc_vnf_state_inst_001:[],tc_vnf_state_inst_002:[],tc_vnf_state_inst_003:[],tc_vnf_state_inst_004:[],tc_vnf_state_inst_005:[],tc_vnf_state_inst_006:[],tc_vnf_state_inst_007:[],tc_vnf_state_start_001:[],tc_vnf_state_start_002:[],tc_vnf_state_start_003:[],tc_vnf_state_stop_001:[],tc_vnf_state_stop_002:[],tc_vnf_state_stop_003:[],tc_vnf_state_term_001:[],tc_vnf_state_term_002:[],tc_vnf_state_term_003:[],tc_vnf_state_term_004:[],tc_vnf_state_term_005:[],tc_vnfc_scale_out_001__em_manu:[],tc_vnfc_scale_out_001__em_ondemand:[],tc_vnfc_scale_out_001__mano_manu:[],tc_vnfc_scale_out_001__mano_ondemand__em_ind:[],tc_vnfc_scale_out_001__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_001__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_001__vnf_manu:[],tc_vnfc_scale_out_001__vnf_ondemand:[],tc_vnfc_scale_out_002__em_manu:[],tc_vnfc_scale_out_002__em_ondemand:[],tc_vnfc_scale_out_002__mano_manu:[],tc_vnfc_scale_out_002__mano_ondemand__em_ind:[],tc_vnfc_scale_out_002__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_002__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_002__vnf_manu:[],tc_vnfc_scale_out_002__vnf_ondemand:[],tc_vnfc_scale_out_003__em_manu:[],tc_vnfc_scale_out_003__em_ondemand:[],tc_vnfc_scale_out_003__mano_manu:[],tc_vnfc_scale_out_003__mano_ondemand__em_ind:[],tc_vnfc_scale_out_003__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_003__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_003__vnf_manu:[],tc_vnfc_scale_out_003__vnf_ondemand:[],tc_vnfc_scale_out_004__em_manual__step_1:[],tc_vnfc_scale_out_004__em_manual__step_max:[],tc_vnfc_scale_out_004__em_ondemand__step_1:[],tc_vnfc_scale_out_004__em_ondemand__step_max:[],tc_vnfc_scale_out_004__mano_manual__step_1:[],tc_vnfc_scale_out_004__mano_manual__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__em_ind__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__em_ind__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__vim_kpi__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__vim_kpi__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__vnf_ind__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__vnf_ind__step_max:[],tc_vnfc_scale_out_004__vnf_manual__step_1:[],tc_vnfc_scale_out_004__vnf_manual__step_max:[],tc_vnfc_scale_out_004__vnf_ondemand__step_1:[],tc_vnfc_scale_out_004__vnf_ondemand__step_max:[],tc_vnfc_scale_out_005__em_manu:[],tc_vnfc_scale_out_005__em_ondemand:[],tc_vnfc_scale_out_005__mano_manu:[],tc_vnfc_scale_out_005__mano_ondemand__em_ind:[],tc_vnfc_scale_out_005__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_005__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_005__vnf_manu:[],tc_vnfc_scale_out_005__vnf_ondemand:[],td_nfv_base_onboard_nsd_001:[],td_nfv_base_teardown_delete_nsd_001:[],td_nfv_fm_vnf_clear_001:[],td_nfv_fm_vnf_notify_001:[],td_nfv_nslcm_instantiate_001:[],td_nfv_nslcm_instantiate_nest_ns_001:[],td_nfv_nslcm_scale_from_level_vnf_001:[],td_nfv_nslcm_scale_in_001:[],td_nfv_nslcm_scale_in_vnf_001:[],td_nfv_nslcm_scale_out_001:[],td_nfv_nslcm_scale_out_vnf_001:[],td_nfv_nslcm_scale_to_level_vnf_001:[],td_nfv_nslcm_terminate_001:[],td_nfv_nslcm_terminate_nested_ns_001:[],td_nfv_nslcm_update_start_001:[],td_nfv_nslcm_update_stop_001:[],td_nfv_nslcm_update_vnf_df_001:[],term:[],termin:[8,20],terminate_tim:[8,20],termination_typ:[8,20],test:[8,20],test_cas:[],than:[8,20],them:[8,20],thi:[1,8,13,20],through:[8,20],time:[8,20],timestamp:[8,20],to_level:[],toler:[4,8,16,20],top_level_script:[],top_level_script_ntt:[],toward:[6,8,18,20],traffic:[0,1,10,11,12,13,22],traffic_config:[8,20],traffic_load:[8,20],trafficadaptererror:[4,16],trafficgenericerror:[8,20],trigger:[8,20],tst:[8,20],tst_007:[],type:[1,8,13,20],ubuntu:[0,1,10,12,13],ubuntuvnfadapt:[6,18],ubuntuvnfadaptererror:[6,18],ui_serv:[],until:[8,20],updat:[8,20],update_tim:[8,20],update_typ:[8,20],update_vnffg:[8,20],updatetyp:[8,20],updatevnffg:[8,20],upload:[8,20],use:[8,20],used:[8,20],useful:[8,20],user:[8,20],user_defined_data:[8,20],uses:[8,20],using:[8,20],util:[],valid:[0,1,2,3,4,5,6,7,8,12,13,14,15,16,17,18,19,20],validate_ns_allocated_vresourc:[8,20],validate_ns_instantiation_level:[8,20],validate_ns_released_vresourc:[8,20],validate_vnf_allocated_vresourc:[8,20],validate_vnf_deployment_flavour:[8,20],validate_vnf_instantiation_level:[8,20],validate_vnf_released_vresourc:[8,20],validate_vnf_vresource_st:[8,20],valu:[1,8,13,20],variou:[8,20],vcpu:[8,20],vdu:[8,20],vendor:[1,8,13,20],verifi:[8,20],verify_ns_sw_imag:[8,20],verify_ns_vnf_instance_count:[8,20],verify_vnf_nsd_map:[8,20],verify_vnf_sw_imag:[8,20],version:[8,20],vim:[0,1,10,11,12,13,22],vim_connection_info:[8,20],vim_id:[8,20],vimadaptererror:[5,17],virtual:[8,20],vmemori:[8,20],vnf1:[8,20],vnf2:[8,20],vnf:[0,1,2,3,4,5,7,10,11,12,13,14,15,16,17,19,22],vnf_change_flavour:[8,20],vnf_configuration_data:[8,20],vnf_create_and_instanti:[8,20],vnf_create_id:[8,20],vnf_delete_id:[8,20],vnf_info:[8,20],vnf_info_fin:[8,20],vnf_info_initi:[8,20],vnf_instance_data:[8,20],vnf_instance_descript:[8,20],vnf_instance_id:[8,20],vnf_instance_nam:[8,20],vnf_instanti:[8,20],vnf_instantiate_sync:[8,20],vnf_instantiate_timeout:[8,20],vnf_lifecycle_change_notification_subscrib:[8,20],vnf_name:[8,20],vnf_oper:[8,20],vnf_operate_sync:[8,20],vnf_queri:[8,20],vnf_scale:[8,20],vnf_scale_sync:[8,20],vnf_scale_timeout:[8,20],vnf_scale_to_level:[8,20],vnf_scale_to_level_sync:[8,20],vnf_stable_state_timeout:[8,20],vnf_start_timeout:[8,20],vnf_stop_timeout:[8,20],vnf_termin:[8,20],vnf_terminate_and_delet:[8,20],vnf_terminate_sync:[8,20],vnf_terminate_timeout:[8,20],vnfadaptererror:[6,18],vnfc:[8,20],vnfc_configuration_data:[8,20],vnfd:[8,20],vnfd_id:[8,20],vnffg:[8,20],vnfgenericerror:[8,20],vnfinfo:[8,20],vnfm:[0,1,6,8,10,12,13,18,20],vnfmadaptererror:[7,19],wait:[8,20],wait_for_notif:[8,20],wait_for_ns_stable_st:[8,20],wait_for_vnf_stable_st:[8,20],well:[8,20],were:[8,20],when:[8,20],whether:[8,20],which:[1,8,13,20],whose:[8,20],within:[8,20],without:[8,20],written:[8,20]},titles:["api package","api.adapter package","api.adapter.em package","api.adapter.mano package","api.adapter.traffic package","api.adapter.vim package","api.adapter.vnf package","api.adapter.vnfm package","api.generic package","api.structures package","Welcome to LCM\u2019s documentation!","api","api package","api.adapter package","api.adapter.em package","api.adapter.mano package","api.adapter.traffic package","api.adapter.vim package","api.adapter.vnf package","api.adapter.vnfm package","api.generic package","api.structures package","api"],titleterms:{adapt:[1,2,3,4,5,6,7,13,14,15,16,17,18,19],api:[0,1,2,3,4,5,6,7,8,9,11,12,13,14,15,16,17,18,19,20,21,22],base:[],cirro:[6,18],cisconfv45:[3,15],cisconfv:[3,15],complex:[],constant:[8,20],constructor:[],content:[0,1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,21],delet:[],document:10,dummi:[3,5,6,7,15,17,18,19],from_level:[],gener:[8,20],indic:10,inst:[],lcm:10,logging_modul:[],mano:[3,8,15,20],map:[],misc:[],modul:[0,1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,21],net:[],object:[9,21],onboard:[],openbaton:[3,15],openstack:[5,17],openwrt:[6,18],out:[],packag:[0,1,2,3,4,5,6,7,8,9,12,13,14,15,16,17,18,19,20,21],ping:[4,16],plugtest:[],report:[],rest_serv:[],rift:[3,15],scale:[],sdl:[3,15],server:[],sphinxf4lcm:[],start:[],state:[],stc:[4,16],stop:[],structur:[9,21],submodul:[2,3,4,5,6,7,8,9,14,15,16,17,18,19,20,21],subpackag:[0,1,12,13],tabl:10,tacker:[2,3,14,15],tc_vnf_complex_001:[],tc_vnf_complex_002:[],tc_vnf_complex_003:[],tc_vnf_scale_out_001__mano_manu:[],tc_vnf_scale_out_001__mano_ondemand__em_ind:[],tc_vnf_scale_out_001__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_001__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_002__mano_manu:[],tc_vnf_scale_out_002__mano_ondemand__em_ind:[],tc_vnf_scale_out_002__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_002__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_003__mano_manu:[],tc_vnf_scale_out_003__mano_ondemand__em_ind:[],tc_vnf_scale_out_003__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_003__mano_ondemand__vnf_ind:[],tc_vnf_scale_out_004__mano_manual__step_1:[],tc_vnf_scale_out_004__mano_manual__step_max:[],tc_vnf_scale_out_004__mano_ondemand__em_ind__step_1:[],tc_vnf_scale_out_004__mano_ondemand__em_ind__step_max:[],tc_vnf_scale_out_004__mano_ondemand__vim_kpi__step_1:[],tc_vnf_scale_out_004__mano_ondemand__vim_kpi__step_max:[],tc_vnf_scale_out_004__mano_ondemand__vnf_ind__step_1:[],tc_vnf_scale_out_004__mano_ondemand__vnf_ind__step_max:[],tc_vnf_scale_out_005__mano_manu:[],tc_vnf_scale_out_005__mano_ondemand__em_ind:[],tc_vnf_scale_out_005__mano_ondemand__vim_kpi:[],tc_vnf_scale_out_005__mano_ondemand__vnf_ind:[],tc_vnf_state_inst_001:[],tc_vnf_state_inst_002:[],tc_vnf_state_inst_003:[],tc_vnf_state_inst_004:[],tc_vnf_state_inst_005:[],tc_vnf_state_inst_006:[],tc_vnf_state_inst_007:[],tc_vnf_state_start_001:[],tc_vnf_state_start_002:[],tc_vnf_state_start_003:[],tc_vnf_state_stop_001:[],tc_vnf_state_stop_002:[],tc_vnf_state_stop_003:[],tc_vnf_state_term_001:[],tc_vnf_state_term_002:[],tc_vnf_state_term_003:[],tc_vnf_state_term_004:[],tc_vnf_state_term_005:[],tc_vnfc_scale_out_001__em_manu:[],tc_vnfc_scale_out_001__em_ondemand:[],tc_vnfc_scale_out_001__mano_manu:[],tc_vnfc_scale_out_001__mano_ondemand__em_ind:[],tc_vnfc_scale_out_001__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_001__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_001__vnf_manu:[],tc_vnfc_scale_out_001__vnf_ondemand:[],tc_vnfc_scale_out_002__em_manu:[],tc_vnfc_scale_out_002__em_ondemand:[],tc_vnfc_scale_out_002__mano_manu:[],tc_vnfc_scale_out_002__mano_ondemand__em_ind:[],tc_vnfc_scale_out_002__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_002__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_002__vnf_manu:[],tc_vnfc_scale_out_002__vnf_ondemand:[],tc_vnfc_scale_out_003__em_manu:[],tc_vnfc_scale_out_003__em_ondemand:[],tc_vnfc_scale_out_003__mano_manu:[],tc_vnfc_scale_out_003__mano_ondemand__em_ind:[],tc_vnfc_scale_out_003__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_003__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_003__vnf_manu:[],tc_vnfc_scale_out_003__vnf_ondemand:[],tc_vnfc_scale_out_004__em_manual__step_1:[],tc_vnfc_scale_out_004__em_manual__step_max:[],tc_vnfc_scale_out_004__em_ondemand__step_1:[],tc_vnfc_scale_out_004__em_ondemand__step_max:[],tc_vnfc_scale_out_004__mano_manual__step_1:[],tc_vnfc_scale_out_004__mano_manual__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__em_ind__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__em_ind__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__vim_kpi__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__vim_kpi__step_max:[],tc_vnfc_scale_out_004__mano_ondemand__vnf_ind__step_1:[],tc_vnfc_scale_out_004__mano_ondemand__vnf_ind__step_max:[],tc_vnfc_scale_out_004__vnf_manual__step_1:[],tc_vnfc_scale_out_004__vnf_manual__step_max:[],tc_vnfc_scale_out_004__vnf_ondemand__step_1:[],tc_vnfc_scale_out_004__vnf_ondemand__step_max:[],tc_vnfc_scale_out_005__em_manu:[],tc_vnfc_scale_out_005__em_ondemand:[],tc_vnfc_scale_out_005__mano_manu:[],tc_vnfc_scale_out_005__mano_ondemand__em_ind:[],tc_vnfc_scale_out_005__mano_ondemand__vim_kpi:[],tc_vnfc_scale_out_005__mano_ondemand__vnf_ind:[],tc_vnfc_scale_out_005__vnf_manu:[],tc_vnfc_scale_out_005__vnf_ondemand:[],td_nfv_base_onboard_nsd_001:[],td_nfv_base_teardown_delete_nsd_001:[],td_nfv_fm_vnf_clear_001:[],td_nfv_fm_vnf_notify_001:[],td_nfv_nslcm_instantiate_001:[],td_nfv_nslcm_instantiate_nest_ns_001:[],td_nfv_nslcm_scale_from_level_vnf_001:[],td_nfv_nslcm_scale_in_001:[],td_nfv_nslcm_scale_in_vnf_001:[],td_nfv_nslcm_scale_out_001:[],td_nfv_nslcm_scale_out_vnf_001:[],td_nfv_nslcm_scale_to_level_vnf_001:[],td_nfv_nslcm_terminate_001:[],td_nfv_nslcm_terminate_nested_ns_001:[],td_nfv_nslcm_update_start_001:[],td_nfv_nslcm_update_stop_001:[],td_nfv_nslcm_update_vnf_df_001:[],term:[],test_cas:[],timestamp:[],to_level:[],top_level_script:[],top_level_script_ntt:[],traffic:[4,8,16,20],tst_007:[],ubuntu:[6,18],ui_serv:[],updat:[],util:[],vim:[5,8,17,20],vnf:[6,8,18,20],vnfm:[7,19],welcom:10}})