#-*- coding: utf-8 -*-
"""
本模块为异常检测算法提供封装器。
"""
import pandas as pd
from sklearn.ensemble import IsolationForest

class IsolationForestAnomalyDetector:
    """
    对scikit-learn的IsolationForest模型进行封装，以便在SWP项目中为异常检测提供一致的接口。
    """

    def __init__(self, n_estimators=100, contamination='auto', random_state=42):
        """
        初始化异常检测器。

        参数:
            n_estimators (int): 集成中的基础估计器数量。
            contamination (float or 'auto'): 数据集的污染程度，即数据集中异常值的比例。
            random_state (int): 控制特征选择和每个分支决策中分割值的伪随机性。
        """
        self.model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1  # 使用所有可用的处理器
        )

    def fit_predict(self, data: pd.DataFrame) -> pd.Series:
        """
        将模型拟合到数据并预测标签（1为正常值，-1为异常值）。

        参数:
            data (pd.DataFrame): 用于拟合模型和预测的输入数据。
                数据应为一个DataFrame，其中每列都是一个特征。

        返回:
            pd.Series: 包含预测结果的Series，其中1表示正常值，-1表示异常值。
                       该Series的索引将与输入数据匹配。
        """
        if not isinstance(data, pd.DataFrame):
            raise TypeError("输入数据必须是pandas DataFrame。")
        if data.empty:
            return pd.Series(dtype=int)

        predictions = self.model.fit_predict(data)
        return pd.Series(predictions, index=data.index)
