#-*- coding: utf-8 -*-
"""
本模块提供了用于在线参数辨识的递归最小二乘（RLS）估计算法的实现。
"""
import numpy as np

class RLSEstimator:
    """
    一个用于在线辨识线性模型 y = phi' * theta 的递归最小二乘（RLS）估计算法。
    """

    def __init__(self, num_params, lambda_=0.99, P0=1000):
        """
        初始化RLS估计算法。

        参数:
            num_params (int): 要估计的参数数量（theta的维度）。
            lambda_ (float, optional): 遗忘因子 (0 < lambda <= 1)。默认为0.99。
            P0 (float, optional): 逆相关矩阵P对角线元素的初始值。
                一个较大的值表示对初始参数估计的置信度较低。默认为1000。
        """
        if not (0 < lambda_ <= 1):
            raise ValueError("遗忘因子lambda必须在0和1之间。")

        self.num_params = num_params
        self.lambda_ = lambda_

        # 初始化参数估计向量theta为零
        self.theta = np.zeros((num_params, 1))

        # 初始化逆相关矩阵P
        self.P = np.eye(num_params) * P0

    def update(self, phi, y):
        """
        使用一个新的数据点更新参数估计。

        参数:
            phi (np.ndarray): 输入向量（回归量向量），形状为 (num_params, 1)。
            y (float): 测量的输出标量。
        """
        phi = phi.reshape(self.num_params, 1) # 确保phi是一个列向量

        # 1. 计算卡尔曼增益向量k
        k_numerator = np.dot(self.P, phi)
        k_denominator = self.lambda_ + np.dot(phi.T, k_numerator)
        k = k_numerator / k_denominator

        # 2. 计算先验估计误差
        y_hat = np.dot(phi.T, self.theta)
        alpha = y - y_hat

        # 3. 更新参数估计向量theta
        self.theta = self.theta + k * alpha

        # 4. 更新逆相关矩阵P
        P_numerator = np.dot(np.eye(self.num_params) - np.dot(k, phi.T), self.P)
        self.P = P_numerator / self.lambda_

    def get_params(self):
        """
        返回当前的参数估计。

        返回:
            np.ndarray: 当前的参数估计向量theta。
        """
        return self.theta.flatten()
