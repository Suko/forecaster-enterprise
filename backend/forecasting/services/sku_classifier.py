"""
SKU Classifier Service

Implements ABC-XYZ classification for demand planning.
Industry standard approach used by SAP, Oracle, Blue Yonder, etc.

ABC Classification: Based on revenue/volume (80/15/5 split)
XYZ Classification: Based on variability (CV thresholds)
Demand Pattern: Regular, Intermittent, Lumpy, Seasonal
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import date
import logging

logger = logging.getLogger(__name__)


@dataclass
class SKUClassification:
    """SKU classification result"""
    item_id: str
    abc_class: str  # A, B, or C
    xyz_class: str  # X, Y, or Z
    demand_pattern: str  # regular, intermittent, lumpy, seasonal
    coefficient_of_variation: float
    average_demand_interval: float
    revenue_contribution: float  # Percentage of total revenue
    forecastability_score: float  # 0.0 to 1.0
    recommended_method: str
    expected_mape_range: Tuple[float, float]
    warnings: List[str]
    metadata: Dict


class SKUClassifier:
    """
    Classifies SKUs using ABC-XYZ analysis.
    
    ABC Classification (Volume):
    - A: Top 80% of revenue (~20% of SKUs)
    - B: Next 15% of revenue (~30% of SKUs)
    - C: Bottom 5% of revenue (~50% of SKUs)
    
    XYZ Classification (Variability):
    - X: CV < 0.5 (low variability)
    - Y: 0.5 ≤ CV < 1.0 (medium variability)
    - Z: CV ≥ 1.0 (high variability)
    
    Demand Patterns:
    - Regular: ADI ≤ 1.32
    - Intermittent: ADI > 1.32
    - Lumpy: ADI > 1.32 AND CV² > 0.49
    """
    
    @staticmethod
    def calculate_abc_classification(
        revenue_dict: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Calculate ABC classification based on revenue.
        
        Args:
            revenue_dict: Dictionary of {item_id: total_revenue}
        
        Returns:
            Dictionary of {item_id: abc_class}
        """
        if not revenue_dict:
            return {}
        
        # Sort by revenue descending
        sorted_skus = sorted(
            revenue_dict.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        total_revenue = sum(revenue_dict.values())
        
        if total_revenue == 0:
            # All zero revenue - classify all as C
            return {sku: "C" for sku, _ in sorted_skus}
        
        classification = {}
        cumulative_revenue = 0
        
        for sku, revenue in sorted_skus:
            cumulative_revenue += revenue
            pct = (cumulative_revenue / total_revenue) * 100
            
            if pct <= 80:
                classification[sku] = "A"
            elif pct <= 95:
                classification[sku] = "B"
            else:
                classification[sku] = "C"
        
        return classification
    
    @staticmethod
    def calculate_xyz_classification(
        cv_dict: Dict[str, float]
    ) -> Dict[str, str]:
        """
        Calculate XYZ classification based on Coefficient of Variation.
        
        Args:
            cv_dict: Dictionary of {item_id: coefficient_of_variation}
        
        Returns:
            Dictionary of {item_id: xyz_class}
        """
        classification = {}
        
        for sku, cv in cv_dict.items():
            if np.isnan(cv) or np.isinf(cv):
                # Invalid CV - classify as Z (high variability)
                classification[sku] = "Z"
            elif cv < 0.5:
                classification[sku] = "X"
            elif cv < 1.0:
                classification[sku] = "Y"
            else:
                classification[sku] = "Z"
        
        return classification
    
    @staticmethod
    def calculate_coefficient_of_variation(series: pd.Series) -> float:
        """
        Calculate Coefficient of Variation (CV = std / mean).
        
        Args:
            series: Pandas Series with demand values
        
        Returns:
            Coefficient of Variation (float)
        """
        if len(series) == 0:
            return float('inf')
        
        # Convert to numeric, handle any non-numeric values
        series = pd.to_numeric(series, errors='coerce')
        series = series.dropna()
        
        if len(series) == 0:
            return float('inf')
        
        mean = series.mean()
        if mean == 0:
            # Zero mean - return high CV
            return float('inf')
        
        std = series.std()
        cv = std / mean
        
        return float(cv)
    
    @staticmethod
    def calculate_average_demand_interval(series: pd.Series) -> float:
        """
        Calculate Average Demand Interval (ADI).
        
        ADI = Total days / Number of non-zero days
        
        ADI > 1.32 indicates intermittent demand.
        
        Args:
            series: Pandas Series with demand values
        
        Returns:
            Average Demand Interval (float)
        """
        if len(series) == 0:
            return float('inf')
        
        total_days = len(series)
        non_zero_days = (series > 0).sum()
        
        if non_zero_days == 0:
            return float('inf')  # No demand at all
        
        adi = total_days / non_zero_days
        return float(adi)
    
    @staticmethod
    def detect_demand_pattern(
        series: pd.Series,
        adi: float,
        cv: float
    ) -> str:
        """
        Detect demand pattern based on ADI and CV.
        
        Patterns:
        - Regular: ADI ≤ 1.32
        - Intermittent: ADI > 1.32
        - Lumpy: ADI > 1.32 AND CV² > 0.49
        
        Args:
            series: Pandas Series with demand values
            adi: Average Demand Interval
            cv: Coefficient of Variation
        
        Returns:
            Pattern name (str)
        """
        if np.isinf(adi) or adi > 1.32:
            # Intermittent or no demand
            cv_squared = cv ** 2
            if cv_squared > 0.49:
                return "lumpy"
            else:
                return "intermittent"
        else:
            return "regular"
    
    @staticmethod
    def calculate_forecastability_score(
        abc_class: str,
        xyz_class: str,
        demand_pattern: str
    ) -> float:
        """
        Calculate forecastability score (0.0 to 1.0).
        
        Higher score = more forecastable.
        
        Args:
            abc_class: A, B, or C
            xyz_class: X, Y, or Z
            demand_pattern: regular, intermittent, or lumpy
        
        Returns:
            Forecastability score (0.0 to 1.0)
        """
        # Base score from ABC class
        abc_scores = {"A": 0.9, "B": 0.7, "C": 0.5}
        base_score = abc_scores.get(abc_class, 0.5)
        
        # Adjust for XYZ class
        xyz_adjustments = {"X": 0.1, "Y": -0.2, "Z": -0.4}
        adjustment = xyz_adjustments.get(xyz_class, 0.0)
        
        # Adjust for demand pattern
        pattern_adjustments = {
            "regular": 0.0,
            "intermittent": -0.2,
            "lumpy": -0.3
        }
        pattern_adjustment = pattern_adjustments.get(demand_pattern, -0.3)
        
        score = base_score + adjustment + pattern_adjustment
        
        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, score))
    
    @staticmethod
    def recommend_method(
        abc_class: str,
        xyz_class: str,
        demand_pattern: str
    ) -> str:
        """
        Recommend forecasting method based on classification.
        
        Args:
            abc_class: A, B, or C
            xyz_class: X, Y, or Z
            demand_pattern: regular, intermittent, or lumpy
        
        Returns:
            Recommended method name (str)
        """
        # Intermittent/lumpy demand → specialized methods
        if demand_pattern == "lumpy":
            return "sba"  # Syntetos-Boylan Approximation
        elif demand_pattern == "intermittent":
            return "croston"  # Croston's method
        
        # Regular demand → route by ABC-XYZ
        combined = f"{abc_class}-{xyz_class}"
        
        routing = {
            # High value, low variability → Best model
            "A-X": "chronos2",
            "B-X": "chronos2",
            "C-X": "chronos2",
            
            # Medium variability → ML with higher safety
            "A-Y": "chronos2",
            "B-Y": "chronos2",
            "C-Y": "ma7",
            
            # High variability → Rules-based or attention
            "A-Z": "chronos2",  # High value, still use ML but flag
            "B-Z": "ma7",
            "C-Z": "min_max",  # Low value, high variability → simple rules
        }
        
        return routing.get(combined, "chronos2")  # Default to Chronos-2
    
    @staticmethod
    def get_expected_mape_range(
        abc_class: str,
        xyz_class: str,
        demand_pattern: str
    ) -> Tuple[float, float]:
        """
        Get expected MAPE range based on classification.
        
        Args:
            abc_class: A, B, or C
            xyz_class: X, Y, or Z
            demand_pattern: regular, intermittent, or lumpy
        
        Returns:
            Tuple of (min_mape, max_mape)
        """
        # Base ranges by ABC-XYZ combination
        # INDUSTRY STANDARD ranges - do not adjust to match our results!
        # These represent what is achievable with good forecasting practices.
        # If we don't meet these, we flag the SKU as "below standard" - not change the standard.
        ranges = {
            "A-X": (10, 25),   # Low variability - excellent forecastability
            "B-X": (15, 30),
            "C-X": (20, 35),
            "A-Y": (20, 40),   # Medium variability - good forecastability
            "B-Y": (25, 45),
            "C-Y": (30, 50),
            "A-Z": (30, 60),   # High variability - moderate forecastability
            "B-Z": (40, 70),
            "C-Z": (50, 100),  # Low value, high variability - acceptable
        }
        
        combined = f"{abc_class}-{xyz_class}"
        base_range = ranges.get(combined, (30, 60))
        
        # Adjust for demand pattern
        if demand_pattern == "intermittent":
            base_range = (base_range[0] + 10, base_range[1] + 20)
        elif demand_pattern == "lumpy":
            base_range = (base_range[0] + 20, base_range[1] + 30)
        
        return base_range
    
    def classify_sku(
        self,
        item_id: str,
        history_df: pd.DataFrame,
        revenue: float,
        total_revenue: float,
        abc_class: Optional[str] = None,
        xyz_class: Optional[str] = None
    ) -> SKUClassification:
        """
        Classify a single SKU.
        
        Args:
            item_id: SKU identifier
            history_df: DataFrame with columns ['date', 'units_sold'] or ['timestamp', 'target']
            revenue: Total revenue for this SKU
            total_revenue: Total revenue across all SKUs (for ABC calculation)
            abc_class: Pre-calculated ABC class (optional)
            xyz_class: Pre-calculated XYZ class (optional)
        
        Returns:
            SKUClassification object
        """
        warnings = []
        
        # Get target column
        target_col = None
        for col in ["units_sold", "target", "sales_qty"]:
            if col in history_df.columns:
                target_col = col
                break
        
        if target_col is None:
            raise ValueError(f"No target column found in history_df. Columns: {history_df.columns.tolist()}")
        
        series = pd.to_numeric(history_df[target_col], errors='coerce').fillna(0)
        
        # Calculate metrics
        cv = self.calculate_coefficient_of_variation(series)
        adi = self.calculate_average_demand_interval(series)
        demand_pattern = self.detect_demand_pattern(series, adi, cv)
        
        # Calculate ABC if not provided
        if abc_class is None:
            revenue_pct = (revenue / total_revenue * 100) if total_revenue > 0 else 0
            if revenue_pct >= 80:
                abc_class = "A"
            elif revenue_pct >= 15:
                abc_class = "B"
            else:
                abc_class = "C"
        
        # Calculate XYZ if not provided
        if xyz_class is None:
            if np.isnan(cv) or np.isinf(cv) or cv >= 1.0:
                xyz_class = "Z"
            elif cv >= 0.5:
                xyz_class = "Y"
            else:
                xyz_class = "X"
        
        # Calculate forecastability
        forecastability_score = self.calculate_forecastability_score(
            abc_class, xyz_class, demand_pattern
        )
        
        # Recommend method
        recommended_method = self.recommend_method(
            abc_class, xyz_class, demand_pattern
        )
        
        # Expected MAPE range
        expected_mape_range = self.get_expected_mape_range(
            abc_class, xyz_class, demand_pattern
        )
        
        # Generate warnings
        if cv >= 1.0:
            warnings.append(f"High variability (CV={cv:.2f}) - forecasts may be less accurate")
        if adi > 1.32:
            warnings.append(f"Intermittent demand (ADI={adi:.2f}) - consider specialized methods")
        if len(series) < 30:
            warnings.append(f"Limited history ({len(series)} days) - forecasts may be less reliable")
        if (series == 0).sum() / len(series) > 0.5:
            warnings.append(f"High zero-demand days ({(series == 0).sum()}/{len(series)})")
        
        # Calculate revenue contribution
        revenue_contribution = (revenue / total_revenue * 100) if total_revenue > 0 else 0
        
        return SKUClassification(
            item_id=item_id,
            abc_class=abc_class,
            xyz_class=xyz_class,
            demand_pattern=demand_pattern,
            coefficient_of_variation=float(cv),
            average_demand_interval=float(adi),
            revenue_contribution=float(revenue_contribution),
            forecastability_score=forecastability_score,
            recommended_method=recommended_method,
            expected_mape_range=expected_mape_range,
            warnings=warnings,
            metadata={
                "total_days": len(series),
                "mean_demand": float(series.mean()),
                "std_demand": float(series.std()),
                "min_demand": float(series.min()),
                "max_demand": float(series.max()),
                "zero_days": int((series == 0).sum()),
                "zero_percentage": float((series == 0).sum() / len(series) * 100),
            }
        )

