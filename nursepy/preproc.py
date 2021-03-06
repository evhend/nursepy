import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder, RobustScaler
from sklearn.compose import ColumnTransformer


def preproc(
        X_train,
        X_test=None,
        auto=False,
        OHE=[],
        standard_scale=[],
        robust_scale=[],
        numerical_impute=[],
        categorical_impute=[],
        label_encode={}):
    """
    Preprocesses data frames, including onehot encoding, scaling, and imputation, and label encoding

    Parameters
    ----------
    X_train (pd dataframe): X_train dateframe - Required
    X_test (pd dataframe): X_test dataframe - Default None
    auto (bool): If true we will automatically decide how to process columns, you must not use the manual settings (standard_scale, robust_scale etc.) if auto is set to true. - Default False
    OHE (list): List  of columns to be processed with sklearn OneHotEncoder, this accepts non numerical categorical rows without need for label encoding. - Default []
    standard_scale (list): List of columns to be processes with standard scalar. - Defualt []
    robust_scale (list): List of columns to be preprocessed with robust scalar. - Defualt []
    numerical_impute (list): list of column names that should be imputed using mean method. - Default []
    categorical_impute (list): list of column names that should be imputed to 'missing'. - Default []
    label_encode (dict): Keys in the dict should be the column names to transform, the values should be lists that
    contain the various values in the column, the order of the values will determine the encoding (1st element will be 0 etc.). - Default {}

    Returns
    -------
    processed pandas dataframes. X_train, X_test

    Examples
    --------
    >>> X_train, X_test = preproc(X_train, X_test, auto=True)
    """
    args = locals().copy()
    arg_types = {
        'X_train': [type(pd.DataFrame())],
        'X_test': [type(None), type(pd.DataFrame())],
        'auto': [type(True)],
        'OHE': [type([]), type(np.array([]))],
        'standard_scale': [type([]), type(np.array([]))],
        'robust_scale': [type([]), type(np.array([]))],
        'numerical_impute': [type([]), type(np.array([]))],
        'categorical_impute': [type([]), type(np.array([]))],
        'label_encode': [type({})]
    }
    # check arg types
    for arg_key in args.keys():
        argument_type = type(args[arg_key])
        if argument_type not in arg_types[arg_key]:
            raise ValueError(
                f"Arg type error. {arg_key} needs to be one of {arg_types[arg_key]}. You passed in type of: {argument_type}")

    X_train = X_train.copy()
    if X_test is not None:
        X_test = X_test.copy()
    # automatically choose which columns to scale and encode
    if auto:
        for element in [
                OHE,
                standard_scale,
                robust_scale,
                numerical_impute,
                categorical_impute]:
            if len(element) > 0:
                raise Exception(
                    f'You cannot manually set {element} when setting auto to true')
        label_keys = label_encode.keys()
        if len(label_keys) > 0:
            raise Exception(
                'You cannot manually set categorical_impute when setting auto to true')
        X_num = X_train.select_dtypes(include=['float64', 'int64'])
        standard_scale = X_num.columns.values
        X_cat = X_train.select_dtypes(
            include=['object', 'bool', 'category'])
        OHE = X_cat.columns.values
        transformer = ColumnTransformer(
            transformers=[
                ('cat_imputer',
                    SimpleImputer(strategy='constant', fill_value='missing'),
                    categorical_impute
                 ),
                ('num_imputer',
                    SimpleImputer(strategy='median'),
                    numerical_impute
                 ),
                ("one_hot",
                    OneHotEncoder(drop='first'),
                    OHE
                 ),
                ("standard_scalar",
                    StandardScaler(),
                    standard_scale
                 ),
                ("robust_scalar",
                    RobustScaler(),
                    robust_scale
                 )
            ],
            remainder='passthrough'  # donot apply anything to the remaining columns
        )
    else:
        transformer = ColumnTransformer(
            transformers=[
                ('cat_imputer',
                    SimpleImputer(strategy='constant', fill_value='missing'),
                    categorical_impute
                 ),
                ('num_imputer',
                    SimpleImputer(strategy='median'),
                    numerical_impute
                 ),
                ("one_hot",
                    OneHotEncoder(),
                    OHE
                 ),
                ("standard_scalar",
                    StandardScaler(),
                    standard_scale
                 ),
                ("robust_scalar",
                    RobustScaler(),
                    robust_scale
                 )
            ],
            remainder='passthrough'  # donot apply anything to the remaining columns
        )
    column_names = X_train.columns
    # fit transformation to the train X set
    transformer.fit(X_train)
    # fetch newly created ohe transformed columns
    if (len(OHE) > 0):
        ohe_columns = transformer.named_transformers_.one_hot.get_feature_names(
            OHE)
    else:
        ohe_columns = []
    # get rid of original OHE columns
    column_names = list(filter(lambda x: x not in OHE, column_names))
    # reset column names with newly created ohe column names
    column_names = np.append(ohe_columns, column_names)
    X_train = pd.DataFrame(data=transformer.transform(
        X_train), columns=column_names)
    # transform test and validation sets if they are included
    if (X_test is not None):
        X_test = pd.DataFrame(data=transformer.transform(
            X_test), columns=column_names)
    # label encoding tranformation
    le_columns = label_encode.keys()
    for column in le_columns:
        le = LabelEncoder()
        le.fit(label_encode[column])
        X_train[column] = le.transform(X_train[column])
        if (X_test is not None):
            X_test[column] = le.transform(X_test[column])
    return X_train, X_test
