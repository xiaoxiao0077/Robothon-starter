"""
Kinematics Module
Forward and inverse kinematics for dexterous hand
"""

import numpy as np

class DexterousHandKinematics:
    """Kinematics for 24-DOF dexterous hand."""
    
    def __init__(self, n_dof=24):
        self.n_dof = n_dof
        
    def forward_kinematics(self, joint_angles):
        """Compute forward kinematics."""
        positions = []
        for i in range(0, len(joint_angles), 3):
            pos = np.array([
                np.cos(joint_angles[i]) * 0.1,
                np.sin(joint_angles[i]) * 0.1,
                joint_angles[i+1] * 0.05
            ])
            positions.append(pos)
        return positions
    
    def inverse_kinematics(self, target_position, initial_angles=None):
        """Compute inverse kinematics."""
        if initial_angles is None:
            angles = np.zeros(self.n_dof)
        else:
            angles = initial_angles.copy()
        
        for _ in range(10):
            current_pos = self.forward_kinematics(angles)[0]
            error = target_position - current_pos
            jacobian = self.compute_jacobian(angles)
            angles += 0.1 * jacobian.T @ error
            
        return angles
    
    def compute_jacobian(self, angles):
        """Compute Jacobian matrix."""
        J = np.zeros((3, self.n_dof))
        J[0, 0] = -np.sin(angles[0]) * 0.1
        J[1, 0] = np.cos(angles[0]) * 0.1
        J[2, 1] = 0.05
        return J
