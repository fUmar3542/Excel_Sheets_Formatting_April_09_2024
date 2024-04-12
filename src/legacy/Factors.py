'''calculating factor betas'''
import logging

import pandas as pd

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

#import _pydevd_bundle

def calculate_position_betas(
    factor_returns: pd.DataFrame,
    position_returns: pd.DataFrame,
) -> pd.DataFrame:
    '''
    Calculates the positions's beta 
    Equity beta is beta vs first column of factor_returns
    Other factors betas are position beta vs factor returns beta Equity adjusted 
    
    Args:
        factor_returns (pd.DataFrame): A DataFrame of factor returns
            long format.
        position_returns (pd.DataFrame): A DataFrame of position returns per day
            long format.
    Returns:
        pd.DataFrame: A DataFrame of adjusted position-level betas for
            each factor, with position names as index and factor names as columns.
    '''

    # Position level beta to each factor
    factor_returns_long = factor_returns\
        .reset_index()\
        .melt(
            id_vars='date',
            var_name='factor',
            value_name='factor_return',
        )
    # print(factor_returns_long)

    position_returns_long = position_returns\
        .reset_index()\
        .rename(
            columns={
                'return': 'position_return',
                'TradeDate': 'date',
                'VaRTicker': 'position'
            }
        )\
        .melt(
            id_vars='date',
            var_name='position',
            value_name='position_return',
        )

    # Merge factor and position returns
    merged_returns = pd.merge(factor_returns_long, position_returns_long, on='date', how='inner')
    mr = merged_returns.reset_index().copy()    #fact_eq = mr[mr['factor']==factor_eq][['date','factor_return']].rename(columns={"factor_return":"eq_return"})

    # natural beta vs factors 
    covar_position_fact = mr.groupby(['position','factor'])[['position_return', 'factor_return']].cov()
    var_df = covar_position_fact.iloc[1::2, 1].reset_index().drop(columns=['level_2']).set_index(['position','factor'])
    covar_df = covar_position_fact.iloc[::2, 1].reset_index().drop(columns=['level_2']).set_index(['position','factor'])
    beta = covar_df/var_df # SLR beta = covariance / variance regressor
    beta.reset_index(inplace=True)
    beta.rename(columns={'factor_return':'beta'},inplace=True)
    beta = pd.pivot_table(data = beta, values='beta',columns='factor', index='position')
    # put columns in same order as factors + rename first column 'ID'
    beta = beta[factor_returns.columns]
    beta.reset_index(inplace=True)
    beta.rename(columns={'position':'ID'},inplace=True)
    
    # get Equity returns
    factor_eq = factor_returns.columns[0] # the Equity Factor is always the first column, cf helper.imply_smb_gmv
    fact_eq = mr[mr['factor']==factor_eq][['date','factor','factor_return']].drop_duplicates().rename(columns={"factor":factor_eq,"factor_return":"eq_return"})
    mr = pd.merge(mr,fact_eq, on = 'date', how='left')

    # beta position vs Equity
    #print(_pydevd_bundle.pydevd_constants.PYDEVD_WARN_EVALUATION_TIMEOUT )
    covar_position_eq = mr[mr['factor']==factor_eq].groupby(['position'])[['position_return', 'eq_return']].cov()
    var_eq = fact_eq['eq_return'].var() #covar_byposition.iloc[1,1]
    beta_eq = covar_position_eq.iloc[::2, 1] / var_eq   # SLR beta = covariance / variance regressor
    beta_eq.index = [ (factor_eq,x) for (x,_) in beta_eq.index]
    
    #adjust factor return: substract beta*equity return 
    covar_byfactor = mr.groupby(['factor'])[['factor_return', 'eq_return']].cov()
    beta_fact_eq = covar_byfactor.iloc[::2, 1] / var_eq   # SLR beta = covaraince / variance regressor    
    beta_fact_eq.index = [ x for (x,_) in beta_fact_eq.index]
    beta_fact_eq.name = 'beta_fact_vs_eq'
    mr = pd.merge(mr,beta_fact_eq, left_on='factor', right_index=True)
    mr.loc[mr['factor']==factor_eq,'beta_fact_vs_eq']=0  # we don't want to orthogonalise the Equity factor ==> put its beta to 0 
    mr['factor_return']=mr['factor_return']-mr['beta_fact_vs_eq']*mr['eq_return']

    # regress positions vs factors 
    covar_byposition = mr.groupby(['factor','position'])[['position_return', 'factor_return']].cov()
    var_eq = covar_byposition.iloc[1::2,1]
    beta_fact = covar_byposition.iloc[1::2, 0] / var_eq   # SLR beta = covaraince / variance regressor
    beta_fact.index = [ (x,y) for (x,y,_) in beta_fact.index]
    beta_fact= beta_fact[[x for x in beta_fact.index if x[0]!=factor_eq]]  # remove the Equity as a factor 
    
    # merge the 2 betas series
    beta_all = pd.concat([beta_eq,beta_fact],axis=0)
    beta_all = pd.DataFrame(beta_all,columns=['beta'])
    beta_all.reset_index(inplace=True)
    beta_all['factor']=beta_all['index'].apply(lambda x:x[0])
    beta_all['position']=beta_all['index'].apply(lambda x:x[1])
    beta_all.drop(columns='index',inplace=True)
    beta_all.set_index('position',inplace=True)
    beta_all = pd.pivot_table(data = beta_all,values='beta',columns='factor', index='position')    
    # arrange columns in same order as factors + name first column 'ID'
    beta_all = beta_all[factor_returns.columns]
    beta_all.index.name = 'ID'
    beta_all.reset_index(inplace=True)
    
    factor_returns_ortho = pd.pivot_table(mr, values = 'factor_return', index = 'date', columns = 'factor' )
    
    return beta_all, factor_returns_ortho[factor_returns.columns], beta

def calculate_beta_factor_numerator(merged_returns):
    '''calculates the numerator to calculate factor betas'''

    return merged_returns\
        .groupby(['factor', 'position'])[['position_rf', 'factor_rf']]\
        .cov()\
        .iloc[::2, 1]

def calculate_beta_factors_denominator(merged_returns):
    '''calculates the denominator to calculate factor betas'''
    return merged_returns.groupby('factor')['factor_rf'].var()
