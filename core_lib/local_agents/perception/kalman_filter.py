#-*- coding: utf-8 -*-
"""
本模块提供了一个标准的卡尔曼滤波器实现。
"""
import numpy as np

class KalmanFilter:
    """
    一个简单的线性卡尔曼滤波器实现。

    假设一个线性状态空间模型：
    x_k = F * x_{k-1} + B * u_k + w_k  (状态方程)
    z_k = H * x_k + v_k                (测量方程)

    其中:
    w_k ~ N(0, Q) (过程噪声)
    v_k ~ N(0, R) (测量噪声)
    """

    def __init__(self, F, B, H, Q, R, x0, P0):
        """
        初始化卡尔曼滤波器。

        参数:
            F (np.ndarray): 状态转移矩阵。
            B (np.ndarray): 控制输入矩阵。
            H (np.ndarray): 测量矩阵。
            Q (np.ndarray): 过程噪声协方差矩阵。
            R (np.ndarray): 测量噪声协方差矩阵。
            x0 (np.ndarray): 初始状态估计。
            P0 (np.ndarray): 初始估计协方差矩阵。
        """
        self.F = F  # 状态转移矩阵
        self.B = B  # 控制输入矩阵
        self.H = H  # 测量矩阵
        self.Q = Q  # 过程噪声协方差
        self.R = R  # 测量噪声协方差

        self.x = x0  # 初始状态估计
        self.P = P0  # 初始估计协方差

        self.n = F.shape[1]  # 状态变量的数量
        self.I = np.eye(self.n) # 单位矩阵

    def predict(self, u=0):
        """
        执行预测步骤。

        参数:
            u (np.ndarray, optional): 控制向量。默认为0。
        """
        # 预测下一状态
        self.x = np.dot(self.F, self.x) + np.dot(self.B, u)
        # 预测误差协方差
        self.P = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q

        return self.x

    def update(self, z):
        """
        执行更新步骤（校正）。

        参数:
            z (np.ndarray): 测量向量。
        """
        # 计算卡尔曼增益
        S = np.dot(self.H, np.dot(self.P, self.H.T)) + self.R
        K = np.dot(np.dot(self.P, self.H.T), np.linalg.inv(S))

        # 用测量值z更新估计
        y = z - np.dot(self.H, self.x)  # 测量残差
        self.x = self.x + np.dot(K, y)

        # 更新误差协方差
        self.P = np.dot(self.I - np.dot(K, self.H), self.P)

        return self.x
