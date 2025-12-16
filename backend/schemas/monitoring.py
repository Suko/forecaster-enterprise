"""
Monitoring and Validation Schemas
"""
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import date


class SystemStatusResponse(BaseModel):
    """System status response"""
    initialized: bool = Field(..., description="True if any data exists")
    has_products: bool = Field(..., description="True if products table has records")
    has_locations: bool = Field(..., description="True if locations table has records")
    has_suppliers: bool = Field(..., description="True if suppliers table has records")
    has_sales_data: bool = Field(..., description="True if ts_demand_daily has records")
    has_stock_levels: bool = Field(..., description="True if stock_levels has records")
    setup_instructions: Optional[str] = Field(None, description="Guidance for first-time setup")
    data_quality: Optional[Dict[str, Any]] = Field(None, description="Basic data quality metrics")
    metrics_validation: Optional[Dict[str, Any]] = Field(None, description="Computed metrics validation status")


class ValidationIssue(BaseModel):
    """Individual validation issue"""
    type: str = Field(..., description="Issue type: error, warning, or info")
    message: str = Field(..., description="Issue message")
    item_id: Optional[str] = Field(None, description="Related item_id if applicable")


class RawDataQualityReport(BaseModel):
    """Raw data quality validation report"""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    info: List[str] = Field(default_factory=list)


class DataCompletenessReport(BaseModel):
    """Data completeness validation report"""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    info: List[str] = Field(default_factory=list)


class ComputedMetricsValidation(BaseModel):
    """Computed metrics validation details"""
    item_id: str
    current_stock: int
    calculated_metrics: Dict[str, Any]
    validation_errors: List[str] = Field(default_factory=list)
    validation_warnings: List[str] = Field(default_factory=list)


class ComputedMetricsReport(BaseModel):
    """Computed metrics validation report"""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    info: List[str] = Field(default_factory=list)
    sample_validations: List[ComputedMetricsValidation] = Field(default_factory=list)
    samples_checked: int = 0


class FrontendConsistencyReport(BaseModel):
    """Frontend-backend consistency validation report"""
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    info: List[str] = Field(default_factory=list)


class ValidationSummary(BaseModel):
    """Validation summary"""
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    is_valid: bool = True


class ValidationReport(BaseModel):
    """Complete validation report"""
    client_id: str
    validation_timestamp: str
    raw_data_quality: RawDataQualityReport
    data_completeness: DataCompletenessReport
    computed_metrics: Optional[ComputedMetricsReport] = None
    frontend_consistency: Optional[FrontendConsistencyReport] = None
    summary: ValidationSummary


class ValidationRequest(BaseModel):
    """Request for data validation"""
    include_computed_metrics: bool = Field(True, description="Include computed metrics validation")
    include_frontend_consistency: bool = Field(True, description="Include frontend-backend consistency checks")

