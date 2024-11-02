def update_escc_values(scc12_values, CS):
    scc12_values["AEB_CmdAct"] = CS.escc_cmd_act
    scc12_values["CF_VSM_Warn"] = CS.escc_aeb_warning
    scc12_values["CF_VSM_DecCmdAct"] = CS.escc_aeb_dec_cmd_act
    scc12_values["CR_VSM_DecCmd"] = CS.escc_aeb_dec_cmd
