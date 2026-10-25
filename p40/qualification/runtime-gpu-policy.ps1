# Fixed numerical coverage for retained native GPU switches. Drivers do not time kernels.
function Get-StrataRuntimeGpuChecks {
    param($Environment)
    $required=@()
    if($Environment.STRATA_IQ_STAGE_TABLES -eq '1' -or $Environment.STRATA_IQ_STAGE_GRID_MMVQ -eq '1'){$required+='iq_multi_parity'}
    if($Environment.STRATA_QFUSE -eq '1' -or $Environment.STRATA_GR_NORM_FAST -eq '1'){$required+=@('gr_parity','gr_multi_parity')}
    $b=$Environment.STRATA_B6_MMVQ_ROWS;$e=$Environment.STRATA_EXPDEC;$r=$Environment.STRATA_EXPDEC_R
    if($b -and $b -notin @('0','1','4','8')){throw 'B6 value lacks reviewed parity coverage.'}
    if($e -and $e -notin @('0','1')){throw 'EXPDEC is0/1.'}
    if($r -and $r -notin @('1','2')){throw 'EXPDEC row count lacks reviewed parity coverage.'}
    if($b -and $b -ne '0'){$required+='b6_runtime_parity'}
    if($e -eq '1'){$required+='expdec_runtime_parity'}
    if($Environment.STRATA_CKPT_PARK_REUSE -eq '1'){$required+='conversation_reuse_identity_test'}
    if($Environment.STRATA_PF_GROUP_SCRATCH -eq '1'){$required+='prefill_group_scratch_parity'}
    if($Environment.STRATA_PF_HC_REGION -and $Environment.STRATA_PF_HC_REGION -ne '0'){throw 'HC region reuse needs a separate prefill lifetime qualification; not selected.'}
    return $required
}
function Get-StrataRuntimeGpuCases {
    param([string]$Target)
    if($Target -eq 'iq_multi_parity'){
        foreach($tables in @(0,1)){foreach($mmvq in @(0,1)){
            [pscustomobject]@{label="tables$tables-mmvq$mmvq";arguments=@();env=@{STRATA_IQ_STAGE_GRID='1';STRATA_IQ_STAGE_TABLES=[string]$tables;STRATA_IQ_STAGE_GRID_MMVQ=[string]$mmvq;STRATA_QFUSE='0';STRATA_GR_NORM_FAST='0'}}
        }}
    }elseif($Target -in @('gr_parity','gr_multi_parity')){
        foreach($fast in @(0,1)){
            [pscustomobject]@{label="qfuse1-fast$fast";arguments=@();env=@{STRATA_IQ_STAGE_GRID='1';STRATA_IQ_STAGE_TABLES='0';STRATA_IQ_STAGE_GRID_MMVQ='0';STRATA_QFUSE='1';STRATA_GR_NORM_FAST=[string]$fast}}
        }
    }elseif($Target -eq 'b6_runtime_parity'){
        foreach($b in @(1,4,8)){
            [pscustomobject]@{label="rows$b";arguments=@('1','0',[string]$b);env=@{STRATA_IQ_STAGE_TABLES='1';STRATA_IQ_STAGE_GRID_MMVQ='1';STRATA_QFUSE='1';STRATA_GR_NORM_FAST='1';STRATA_B6_MMVQ_ROWS='0';STRATA_EXPDEC='0';STRATA_PARITY_OUTPUT=$null}}
        }
    }elseif($Target -eq 'expdec_runtime_parity'){
        foreach($grid in @(0,1)){
            [pscustomobject]@{label="grid$grid";arguments=@('20','0','20','18/20,18/42,21/20,21/42,22/20,22/42,23/20','def,dec,dec:r2','real',[string]$grid);env=@{STRATA_IQ_STAGE_TABLES='1';STRATA_IQ_STAGE_GRID_MMVQ='1';STRATA_QFUSE='1';STRATA_GR_NORM_FAST='1';STRATA_EXPDEC='0';STRATA_EXPDEC_R='1';STRATA_PARITY_OUTPUT=$null}}
        }
    }elseif($Target -eq 'mmq_tile_parity'){
        [pscustomobject]@{label='actual-formats';arguments=@();env=@{STRATA_PARITY_OUTPUT=$null}}
    }else{[pscustomobject]@{label='standard';arguments=@();env=@{}}}
}
