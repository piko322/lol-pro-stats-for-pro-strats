import pandas as pd
import numpy as np



def _filter_period(series:pd.Series, period:list=[-1,9999999]):
    if type(period[0]) != str:
        return series.between(period[0], period[1])
    return series.isin(period)

def filter_df_in_period(df:pd.DataFrame, filter_dict:dict, return_filter:bool=False) -> pd.DataFrame or np.ndarray:
    """
    Filters a pandas dataframe based on a dictionary of column names and periods. 
    The dictionary should be in the form {column_name: [[period], inverse]}. Refer to the example below.
    If the period is a list of strings, the filter will accept all values that are in the list. 
    If it's a numerical list, the filter will accept all values that are in the range of the list.
    If inverse is True, the filter will be inverted. If not specified, it defaults to False (returns the normal, non-inverted filter).
    If return_filter is True, returns a boolean mask of the dataframe instead of the dataframe itself. This is useful for
    when you want to apply the same filter to multiple dataframes.

    
    Args:
        df (pd.DataFrame): The dataframe to be filtered or to be used as a mask
        dictionary (dict): The dictionary of column names and periods, in the format 
            {
                column_name_1: [[period_1], inverse_1],\n
                column_name_2: [[period_2], inverse_2],
            }
        return_filter (bool, optional): Returns the mask filter if True. Defaults to False.

    Returns:
        pd.DataFrame or np.ndarray: If return_filter is False, returns the filtered dataframe. 
        Else, returns the mask used to filter the dataframe.
        
        
    Example:
        >>> filter_dict = {
                'column_name_1': [[period_1], inverse_1],\n
                'column_name_2': [[period_2], inverse_2],
            }
        >>> mask = filter_df_in_period(df, filter_dict, return_filter=True)
        >>> df = df[mask]
        OR
        >>> df = filter_df_in_period(df, filter_dict)
    """
    if not return_filter:
        for k,v in filter_dict.items():
            period = v[0]
            inverse = v[1] if len(v) > 1 else False
            if not inverse:
                df = df[_filter_period(df[k], period)]
            else:
                df = df[~_filter_period(df[k], period)]
        return df
    else:
        # Returns the mask used to filter the df
        mask = np.ones(len(df), dtype=bool)
        for k,v in filter_dict.items():
            period = v[0]
            inverse = v[1] if len(v) > 1 else False
            if not inverse:
                mask = mask & _filter_period(df[k], period)
            else:
                mask = mask & ~_filter_period(df[k], period)
        return mask