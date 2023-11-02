from numbers import Number
from typing import Literal, Optional, Sequence, Union

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

from eis_toolkit import exceptions
from eis_toolkit.checks.dataframe import check_columns_valid


def one_hot_encode(
    data: Union[pd.DataFrame, np.ndarray],
    columns: Optional[Sequence[str]] = None,
    drop_encoded_columns=True,
    drop_category: Optional[Literal["first", "if_binary"]] = None,
    sparse_output: bool = True,
    out_dtype: Union[type, np.dtype] = int,
    handle_unknown: Literal["error", "ignore", "infrequent_if_exist"] = "infrequent_if_exist",
    min_frequency: Optional[Number] = None,
    max_categories: Optional[int] = None,
) -> Union[pd.DataFrame, np.ndarray]:
    """
    Perform one-hot (or one-of-K or dummy) encoding on categorical data in a DataFrame or NumPy array.

    This function converts categorical variables into a form that could be provided to machine learning
    algorithms for better prediction. For each unique category in the feature, a new binary column is created.

    Continuous data should not be given to this function to avoid excessive amounts of binary features. If input
    is a DataFrame, continuous data can be excluded from encoding by specifying columns to encode.

    The function allows control over aspects like handling unknown categories, controlling sparsity of the output,
    and setting data type of the encoded columns.

    Args:
        data: Input data as a DataFrame or Numpy array. If a DataFrame is provided, the operation can be
            restricted to specified columns.
        columns: Specifies the columns to encode if 'data' is a DataFrame. If None, all columns are
            considered for encoding. Ignored if 'data' is a Numpy array.
        drop_encoded_columns: If True and 'data' is a DataFrame, the original columns being encoded will
            be dropped from the output. Defaults to True.
        drop_category: Specifies a method to drop one of the categories to avoid multicollinearity.
            'first' drops the first category, 'if_binary' drops one category only if the feature is binary.
            If None, no category is dropped. Defaults to None.
        sparse_output: Determines whether the output matrix is sparse or dense. Defaults to True (sparse).
        out_dtype: Numeric data type of the output. Default to int.
        handle_unknown: Specifies how to handle unknown categories encountered during transform. 'error' raises
            an error, 'ignore' ignores unknown categories, and 'infrequent_if_exist' treats them as infrequent.
        min_frequency: The minimum frequency (as a float or an int) needed to include a category in encoding.
        max_categories: The maximum number of categories to include in encoding.

    Returns:
        Encoded data in the form of a DataFrame if input was a DataFrame, or a NumPy array (dense or sparse)
            if input was a NumPy array.

    Raises:
        EmptyDataFrameException: If the input DataFrame is empty.
        InvalidDatasetException: If the input NumPy array is empty.
        InvalidColumnException: If any specified column to encode does not exist in the input DataFrame.
    """
    is_dataframe = isinstance(data, pd.DataFrame)
    if is_dataframe:
        if data.empty:
            raise exceptions.EmptyDataFrameException("Input DataFrame is empty.")
        df = data.copy()
    else:
        if data.size == 0:
            raise exceptions.InvalidDatasetException("Input array is empty.")
        df = pd.DataFrame(data)

    if columns is not None:
        if not check_columns_valid(df, columns):
            raise exceptions.InvalidColumnException("All selected columns were not found in the input DataFrame.")
        transform_df = df[columns]
    else:
        transform_df = df

    encoder = OneHotEncoder(
        drop=drop_category,
        sparse_output=sparse_output,
        dtype=out_dtype,
        handle_unknown=handle_unknown,
        min_frequency=min_frequency,
        max_categories=max_categories,
        feature_name_combiner=lambda feature, category: str(feature) + "_" + str(category),
    )

    # Transform selected columns
    encoded_data = encoder.fit_transform(transform_df)
    encoded_cols = encoder.get_feature_names_out(transform_df.columns)

    # If input was a DataFrame, create output DataFrame
    if is_dataframe:
        if sparse_output:
            encoded_df = pd.DataFrame.sparse.from_spmatrix(encoded_data, columns=encoded_cols, index=df.index)
        else:
            encoded_df = pd.DataFrame(encoded_data, columns=encoded_cols, index=df.index)

        if drop_encoded_columns:
            df = df.drop(transform_df.columns, axis=1)

        encoded_data = pd.concat([df, encoded_df], axis=1)

    return encoded_data
