"""Reusable preprocessing for churn modeling."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

TARGET_COLUMN = "churn"

NUMERIC_FEATURES = [
    "age",
    "tenure_months",
    "monthly_fee",
    "total_spent",
    "support_calls",
    "complaints",
    "last_payment_delay",
    "digital_usage_score",
    "marketing_score",
    "preferred_contact_hour",
]

CATEGORICAL_FEATURES = [
    "gender",
    "region",
    "customer_segment",
    "contract_type",
    "internet_service",
    "tv_service",
    "streaming_service",
    "payment_method",
]

DROP_COLUMNS = [
    "customer_id",
    "internal_campaign_code",
]


@dataclass(frozen=True)
class FeatureSchema:
    numeric_features: tuple[str, ...]
    categorical_features: tuple[str, ...]
    drop_columns: tuple[str, ...]
    target_column: str

    @property
    def model_features(self) -> tuple[str, ...]:
        """Return numeric and categorical feature names in model order.

        Returns:
            Tuple of numeric names followed by categorical names.
        """
        return self.numeric_features + self.categorical_features


def get_feature_schema() -> FeatureSchema:
    """Return the immutable numeric, categorical and target schema.

    Returns:
        FeatureSchema describing input columns and the churn target.
    """
    return FeatureSchema(
        numeric_features=tuple(NUMERIC_FEATURES),
        categorical_features=tuple(CATEGORICAL_FEATURES),
        drop_columns=tuple(DROP_COLUMNS),
        target_column=TARGET_COLUMN,
    )


def validate_feature_columns(
    dataframe: pd.DataFrame,
    *,
    require_target: bool = True,
) -> None:
    """Check required model columns; raise ValueError for missing columns.

    Args:
        dataframe: Customer rows with the required feature columns.
        require_target: Whether the churn target column is required.

    Returns:
        None; raises ValueError when required columns are missing.
    """
    schema = get_feature_schema()
    required = set(schema.model_features)

    if require_target:
        required.add(schema.target_column)

    missing = sorted(required - set(dataframe.columns))
    if missing:
        raise ValueError(f"Missing modeling columns: {missing}")


def split_features_target(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """Return copied model features and the integer churn target.

    Args:
        dataframe: Customer rows with the required feature columns.

    Returns:
        Tuple of copied feature DataFrame and integer target Series.
    """
    validate_feature_columns(dataframe, require_target=True)
    schema = get_feature_schema()

    features = dataframe.loc[:, list(schema.model_features)].copy()
    target = dataframe[schema.target_column].astype(int).copy()

    return features, target


def select_inference_features(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """Return copied model features without requiring a target.

    Args:
        dataframe: Customer rows with the required feature columns.

    Returns:
        DataFrame containing only model features in schema order.
    """
    validate_feature_columns(dataframe, require_target=False)
    schema = get_feature_schema()
    return dataframe.loc[:, list(schema.model_features)].copy()


def build_preprocessing_pipeline() -> ColumnTransformer:
    """Return an unfitted numeric and categorical ColumnTransformer.

    Returns:
        Unfitted ColumnTransformer with numeric and categorical pipelines.
    """
    schema = get_feature_schema()

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, list(schema.numeric_features)),
            (
                "categorical",
                categorical_pipeline,
                list(schema.categorical_features),
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )
