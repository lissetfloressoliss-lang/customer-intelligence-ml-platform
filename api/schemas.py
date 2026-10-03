"""Complete inference contract for the 18 original model features."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

Nonnegative = Annotated[float, Field(ge=0, allow_inf_nan=False)]
Score = Annotated[float, Field(ge=0, le=100, allow_inf_nan=False)]


class CustomerInput(BaseModel):
    """All features are required; explicit nulls use persisted imputers."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    customer_id: str = Field(min_length=1, max_length=100)
    age: Nonnegative | None
    tenure_months: int = Field(ge=0)
    monthly_fee: Nonnegative | None
    total_spent: Nonnegative | None
    support_calls: int = Field(ge=0)
    complaints: int = Field(ge=0)
    last_payment_delay: int = Field(ge=0)
    digital_usage_score: Score | None
    marketing_score: Score | None
    preferred_contact_hour: int = Field(ge=0, le=23)
    gender: Literal["Femenino", "Masculino"] | None
    region: Literal["Lima", "Norte", "Centro", "Sur", "Oriente"] | None
    customer_segment: Literal["Masivo", "Joven digital", "Familia", "Premium"] | None
    contract_type: Literal["Mensual", "Anual", "Bianual"] | None
    internet_service: Literal["Fibra", "DSL", "Sin internet"] | None
    tv_service: Literal["Sí", "No"] | None
    streaming_service: Literal["Sí", "No"] | None
    payment_method: (
        Literal["Tarjeta", "Débito automático", "Transferencia", "Efectivo"] | None
    )


class PredictionOutput(BaseModel):
    """Prediction at configured threshold; no ground-truth claim."""

    customer_id: str
    churn_probability: float = Field(ge=0, le=1)
    churn_prediction: Literal[0, 1]
