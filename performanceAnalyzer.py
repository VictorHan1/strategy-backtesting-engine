from dataclasses import dataclass, field
from typing import Dict
import numpy as np
import pandas as pd


@dataclass
class PerformanceAnalyzer:
    """
    Compute basic performance statistics for a trade list.
    total trades, win rate, average risk-reward ratio, and average return.
    Attributes:
        trades (pd.DataFrame): DataFrame containing trade data with required columns.
        return_col (str): Name of the column containing return percentages.
        rr_col (str): Name of the column containing risk-reward ratios.
        _stats (Dict[str, float]): Computed statistics from the trades.
    """

    trades: pd.DataFrame
    _stats: Dict[str, float] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._calculate_stats()

    @property # used to access stats in a more Pythonic way like analyzer.stats
    def stats(self) -> Dict[str, float]:
        """Dictionary of computed statistics (shallow copy)."""
        return dict(self._stats)

    def _calculate_stats(self) -> None:
        returns = self.trades["return_pct"]  # 'return_pct' is the column with return percentages
        wins = returns[returns > 0]
        losses = returns[returns < 0]

        total_gain = wins.sum()
        total_loss = abs(losses.sum())

        rr_overall = total_gain / total_loss if total_loss != 0 else np.nan  # Avoid division by zero

        self._stats = {
            "total_trades": int(len(returns)),
            "win_rate": float((returns > 0).mean()),  # proportion of trades with positive return
            "avg_rr": float(rr_overall),
            "avg_return": float(returns.mean()),
        }
