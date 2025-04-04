'''utilitity functions for var calculations'''
import numpy as np
import pandas as pd
from src.handles.exception_handling import MyExceptions


def imply_SMB_GMV(factor_returns: pd.DataFrame) -> pd.DataFrame:
    try:
        # imply Small - Big, Growth - Value
        factor_returns["RIY less RTY"] = (
            factor_returns["RIY Index"] - factor_returns["RTY Index"]
        )
        factor_returns["RAG less RAV"] = (
            factor_returns["RAG Index"] - factor_returns["RAV Index"]
        )
        factor_returns = factor_returns[
            [
                "LD12TRUU Index",
                "SPX Index",
                "RIY less RTY",
                "RAG less RAV",
            ]
            + [
                col
                for col in factor_returns.columns
                if col
                not in [
                    "LD12TRUU Index",
                    "SPX Index",
                    "RIY Index",
                    "RTY Index",
                    "RAG Index",
                    "RAV Index",
                    "RIY less RTY",
                    "RAG less RAV",
                ]
            ]
        ]
    except Exception as ex:
        MyExceptions.show_message(tab='var_utils.py',
                                  message="Following exception occurred during calculating factor returns\n\n" + str(
                                      ex))
    finally:
        return factor_returns


def multiply_matrices(
    matrix_cov: pd.DataFrame,
    exposure: pd.DataFrame,
    factor_betas: pd.DataFrame
) -> pd.DataFrame:
    '''
    matrix multiplication to calculate VaR

    Args:
        matrix_cov: pd.DataFrame
        exposure: pd.DataFrame
        factor_betas_fund: pd.DataFrame
    '''
    position_exposure = None
    try:
        exposure_t = exposure.T
        factor_betas_t = factor_betas.T

        position_exposure = exposure_t\
            .dot(factor_betas)\
            .dot(matrix_cov)\
            .dot(factor_betas_t)\
            .T
        # .dot(exposure)
    except Exception as ex:
        MyExceptions.show_message(tab='var_utils.py',
                                  message="Following exception occurred during calculating position exposure\n\n" + str(
                                      ex))
    finally:
        return (position_exposure ** .5)


def correlation_matrix(
    factor_returns: pd.DataFrame,
    factor: pd.DataFrame,
) -> pd.DataFrame:
    '''calculates factor correlation matrix'''
    factor_correl = None
    try:
        factor_returns = imply_SMB_GMV(factor_returns)
        factor_correl = factor_returns.corr()
        factor.set_index(["FactorID"], inplace=True)
        factor_correl = pd.merge(
            factor_correl, factor["Factor Names"],
            left_index=True,
            right_index=True,
        )
        factor_correl.reset_index(inplace=True, drop=True)
        factor_correl.set_index(["Factor Names"], inplace=True)
        # factor_correl.columns = factor_correl.index
    except Exception as ex:
        MyExceptions.show_message(tab='var_utils.py',
                                  message="Following exception occurred during calculating factor correlation\n\n" + str(
                                      ex))
    finally:
        return factor_correl


def decay_covariance_matrix(factor_returns: pd.DataFrame) -> pd.DataFrame:
    '''calculates covariance matrix with decay function'''
    factor_covar_decay = None
    try:
        intervals = np.linspace(start=1, stop=len(
            factor_returns), num=len(factor_returns))
        data = ((1 - 0.94) * 0.94 ** (intervals - 1)) ** (0.5)  # type: ignore
        df_tmp = np.repeat(data, len(factor_returns.columns))
        df_tmp = df_tmp.reshape(len(data), len(factor_returns.columns))
        factor_returns_decay = factor_returns * df_tmp
        factor_covar_decay = factor_returns_decay.cov()
    except Exception as ex:
        MyExceptions.show_message(tab='var_utils.py',
                                  message="Following exception occurred during calculating factor coverance decay\n\n" + str(
                                      ex))
    finally:
        return factor_covar_decay


def covariance_matrix(factor_returns: pd.DataFrame) -> pd.DataFrame:
    '''calculates covariance matrix betweem factor returns'''

    factor_cov = factor_returns.cov()
    return factor_cov
