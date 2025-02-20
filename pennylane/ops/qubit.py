# Copyright 2018-2021 Xanadu Quantum Technologies Inc.

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
This module contains the available built-in discrete-variable
quantum operations supported by PennyLane, as well as their conventions.
"""
import cmath
import functools

# pylint:disable=abstract-method,arguments-differ,protected-access
import math
import numpy as np
from scipy.linalg import block_diag

import pennylane as qml
from pennylane.operation import AnyWires, DiagonalOperation, Observable, Operation
from pennylane.templates.decorator import template
from pennylane.templates.state_preparations import BasisStatePreparation, MottonenStatePreparation
from pennylane.utils import expand, pauli_eigs
from pennylane.wires import Wires

INV_SQRT2 = 1 / math.sqrt(2)


class AdjointError(Exception):
    """Exception for non-adjointable operations."""

    pass


class Hadamard(Observable, Operation):
    r"""Hadamard(wires)
    The Hadamard operator

    .. math:: H = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 & 1\\ 1 & -1\end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None
    eigvals = pauli_eigs(1)
    matrix = np.array([[INV_SQRT2, INV_SQRT2], [INV_SQRT2, -INV_SQRT2]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @classmethod
    def _eigvals(cls, *params):
        return cls.eigvals

    def diagonalizing_gates(self):
        r"""Rotates the specified wires such that they
        are in the eigenbasis of the Hadamard operator.

        For the Hadamard operator,

        .. math:: H = U^\dagger Z U

        where :math:`U = R_y(-\pi/4)`.

        Returns:
            list(~.Operation): A list of gates that diagonalize Hadamard in
            the computational basis.
        """
        return [RY(-np.pi / 4, wires=self.wires)]

    @staticmethod
    def decomposition(wires):
        decomp_ops = [
            PhaseShift(np.pi / 2, wires=wires),
            RX(np.pi / 2, wires=wires),
            PhaseShift(np.pi / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return Hadamard(wires=self.wires)


class PauliX(Observable, Operation):
    r"""PauliX(wires)
    The Pauli X operator

    .. math:: \sigma_x = \begin{bmatrix} 0 & 1 \\ 1 & 0\end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None
    eigvals = pauli_eigs(1)
    matrix = np.array([[0, 1], [1, 0]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @classmethod
    def _eigvals(cls, *params):
        return cls.eigvals

    def diagonalizing_gates(self):
        r"""Rotates the specified wires such that they
        are in the eigenbasis of the Pauli-X operator.

        For the Pauli-X operator,

        .. math:: X = H^\dagger Z H.

        Returns:
            list(qml.Operation): A list of gates that diagonalize PauliY in the
            computational basis.
        """
        return [Hadamard(wires=self.wires)]

    @staticmethod
    def decomposition(wires):
        decomp_ops = [
            PhaseShift(np.pi / 2, wires=wires),
            RX(np.pi, wires=wires),
            PhaseShift(np.pi / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return PauliX(wires=self.wires)

    def _controlled(self, wire):
        CNOT(wires=Wires(wire) + self.wires)


class PauliY(Observable, Operation):
    r"""PauliY(wires)
    The Pauli Y operator

    .. math:: \sigma_y = \begin{bmatrix} 0 & -i \\ i & 0\end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None
    eigvals = pauli_eigs(1)
    matrix = np.array([[0, -1j], [1j, 0]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @classmethod
    def _eigvals(cls, *params):
        return cls.eigvals

    def diagonalizing_gates(self):
        r"""Rotates the specified wires such that they
        are in the eigenbasis of PauliY.

        For the Pauli-Y observable,

        .. math:: Y = U^\dagger Z U

        where :math:`U=HSZ`.

        Returns:
            list(~.Operation): A list of gates that diagonalize PauliY in the
                computational basis.
        """
        return [PauliZ(wires=self.wires), S(wires=self.wires), Hadamard(wires=self.wires)]

    @staticmethod
    def decomposition(wires):
        decomp_ops = [
            PhaseShift(np.pi / 2, wires=wires),
            RY(np.pi, wires=wires),
            PhaseShift(np.pi / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return PauliY(wires=self.wires)

    def _controlled(self, wire):
        CY(wires=Wires(wire) + self.wires)


class PauliZ(Observable, DiagonalOperation):
    r"""PauliZ(wires)
    The Pauli Z operator

    .. math:: \sigma_z = \begin{bmatrix} 1 & 0 \\ 0 & -1\end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None
    eigvals = pauli_eigs(1)
    matrix = np.array([[1, 0], [0, -1]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @classmethod
    def _eigvals(cls, *params):
        return cls.eigvals

    def diagonalizing_gates(self):
        return []

    @staticmethod
    def decomposition(wires):
        decomp_ops = [PhaseShift(np.pi, wires=wires)]
        return decomp_ops

    def adjoint(self):
        return PauliZ(wires=self.wires)

    def _controlled(self, wire):
        CZ(wires=Wires(wire) + self.wires)


class S(DiagonalOperation):
    r"""S(wires)
    The single-qubit phase gate

    .. math:: S = \begin{bmatrix}
                1 & 0 \\
                0 & i
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None

    @classmethod
    def _matrix(cls, *params):
        return np.array([[1, 0], [0, 1j]])

    @classmethod
    def _eigvals(cls, *params):
        return np.array([1, 1j])

    @staticmethod
    def decomposition(wires):
        decomp_ops = [PhaseShift(np.pi / 2, wires=wires)]
        return decomp_ops

    def adjoint(self):
        return S(wires=self.wires).inv()


class T(DiagonalOperation):
    r"""T(wires)
    The single-qubit T gate

    .. math:: T = \begin{bmatrix}
                1 & 0 \\
                0 & e^{\frac{i\pi}{4}}
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None

    @classmethod
    def _matrix(cls, *params):
        return np.array([[1, 0], [0, cmath.exp(1j * np.pi / 4)]])

    @classmethod
    def _eigvals(cls, *params):
        return np.array([1, cmath.exp(1j * np.pi / 4)])

    @staticmethod
    def decomposition(wires):
        decomp_ops = [PhaseShift(np.pi / 4, wires=wires)]
        return decomp_ops

    def adjoint(self):
        return T(wires=self.wires).inv()


class SX(Operation):
    r"""SX(wires)
    The single-qubit Square-Root X operator.

    .. math:: SX = \sqrt{X} = \frac{1}{2} \begin{bmatrix}
            1+i &   1-i \\
            1-i &   1+i \\
        \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 0

    Args:
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 0
    num_wires = 1
    par_domain = None

    @classmethod
    def _matrix(cls, *params):
        return 0.5 * np.array([[1 + 1j, 1 - 1j], [1 - 1j, 1 + 1j]])

    @classmethod
    def _eigvals(cls, *params):
        return np.array([1, 1j])

    @staticmethod
    def decomposition(wires):
        decomp_ops = [
            RZ(np.pi / 2, wires=wires),
            RY(np.pi / 2, wires=wires),
            RZ(-np.pi, wires=wires),
            PhaseShift(np.pi / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return SX(wires=self.wires).inv()


class CNOT(Operation):
    r"""CNOT(wires)
    The controlled-NOT operator

    .. math:: CNOT = \begin{bmatrix}
            1 & 0 & 0 & 0 \\
            0 & 1 & 0 & 0\\
            0 & 0 & 0 & 1\\
            0 & 0 & 1 & 0
        \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the wires the operation acts on
    """
    num_params = 0
    num_wires = 2
    par_domain = None
    matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])

    @classmethod
    def _matrix(cls, *params):
        return CNOT.matrix

    def adjoint(self):
        return CNOT(wires=self.wires)

    def _controlled(self, wire):
        Toffoli(wires=Wires(wire) + self.wires)


class CZ(DiagonalOperation):
    r"""CZ(wires)
    The controlled-Z operator

    .. math:: CZ = \begin{bmatrix}
            1 & 0 & 0 & 0 \\
            0 & 1 & 0 & 0\\
            0 & 0 & 1 & 0\\
            0 & 0 & 0 & -1
        \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the wires the operation acts on
    """
    num_params = 0
    num_wires = 2
    par_domain = None
    eigvals = np.array([1, 1, 1, -1])
    matrix = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @classmethod
    def _eigvals(cls, *params):
        return cls.eigvals

    def adjoint(self):
        return CZ(wires=self.wires)


class CY(Operation):
    r"""CY(wires)
    The controlled-Y operator

    .. math:: CY = \begin{bmatrix}
            1 & 0 & 0 & 0 \\
            0 & 1 & 0 & 0\\
            0 & 0 & 0 & -i\\
            0 & 0 & i & 0
        \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the wires the operation acts on
    """
    num_params = 0
    num_wires = 2
    par_domain = None
    matrix = np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, -1j],
            [0, 0, 1j, 0],
        ]
    )

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    @staticmethod
    def decomposition(wires):
        decomp_ops = [CRY(np.pi, wires=wires), S(wires=wires[0])]
        return decomp_ops

    def adjoint(self):
        return CY(wires=self.wires)


class SWAP(Operation):
    r"""SWAP(wires)
    The swap operator

    .. math:: SWAP = \begin{bmatrix}
            1 & 0 & 0 & 0 \\
            0 & 0 & 1 & 0\\
            0 & 1 & 0 & 0\\
            0 & 0 & 0 & 1
        \end{bmatrix}.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the wires the operation acts on
    """
    num_params = 0
    num_wires = 2
    par_domain = None
    matrix = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    def adjoint(self):
        return SWAP(wires=self.wires)

    def _controlled(self, wire):
        CSWAP(wires=wire + self.wires)


class CSWAP(Operation):
    r"""CSWAP(wires)
    The controlled-swap operator

    .. math:: CSWAP = \begin{bmatrix}
            1 & 0 & 0 & 0 & 0 & 0 & 0 & 0 \\
            0 & 1 & 0 & 0 & 0 & 0 & 0 & 0 \\
            0 & 0 & 1 & 0 & 0 & 0 & 0 & 0 \\
            0 & 0 & 0 & 1 & 0 & 0 & 0 & 0 \\
            0 & 0 & 0 & 0 & 1 & 0 & 0 & 0 \\
            0 & 0 & 0 & 0 & 0 & 0 & 1 & 0 \\
            0 & 0 & 0 & 0 & 0 & 1 & 0 & 0 \\
            0 & 0 & 0 & 0 & 0 & 0 & 0 & 1
        \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 3
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the wires the operation acts on
    """
    num_params = 0
    num_wires = 3
    par_domain = None
    matrix = np.array(
        [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 0, 1, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
        ]
    )

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    def adjoint(self):
        return CSWAP(wires=self.wires)


class Toffoli(Operation):
    r"""Toffoli(wires)
    Toffoli (controlled-controlled-X) gate.

    .. math::

        Toffoli =
        \begin{pmatrix}
        1 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
        0 & 1 & 0 & 0 & 0 & 0 & 0 & 0\\
        0 & 0 & 1 & 0 & 0 & 0 & 0 & 0\\
        0 & 0 & 0 & 1 & 0 & 0 & 0 & 0\\
        0 & 0 & 0 & 0 & 1 & 0 & 0 & 0\\
        0 & 0 & 0 & 0 & 0 & 1 & 0 & 0\\
        0 & 0 & 0 & 0 & 0 & 0 & 0 & 1\\
        0 & 0 & 0 & 0 & 0 & 0 & 1 & 0
        \end{pmatrix}

    **Details:**

    * Number of wires: 3
    * Number of parameters: 0

    Args:
        wires (Sequence[int]): the subsystem the gate acts on
    """
    num_params = 0
    num_wires = 3
    par_domain = None
    matrix = np.array(
        [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0, 1, 0, 0, 0, 0, 0, 0],
            [0, 0, 1, 0, 0, 0, 0, 0],
            [0, 0, 0, 1, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 0, 0, 0],
            [0, 0, 0, 0, 0, 1, 0, 0],
            [0, 0, 0, 0, 0, 0, 0, 1],
            [0, 0, 0, 0, 0, 0, 1, 0],
        ]
    )

    @classmethod
    def _matrix(cls, *params):
        return cls.matrix

    def adjoint(self):
        return Toffoli(wires=self.wires)


class RX(Operation):
    r"""RX(phi, wires)
    The single qubit X rotation

    .. math:: R_x(\phi) = e^{-i\phi\sigma_x/2} = \begin{bmatrix}
                \cos(\phi/2) & -i\sin(\phi/2) \\
                -i\sin(\phi/2) & \cos(\phi/2)
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(R_x(\phi)) = \frac{1}{2}\left[f(R_x(\phi+\pi/2)) - f(R_x(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`R_x(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 1
    num_wires = 1
    par_domain = "R"
    grad_method = "A"
    generator = [PauliX, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        js = 1j * math.sin(-theta / 2)

        return np.array([[c, js], [js, c]])

    def adjoint(self):
        return RX(-self.data[0], wires=self.wires)

    def _controlled(self, wire):
        CRX(*self.parameters, wires=wire + self.wires)


class RY(Operation):
    r"""RY(phi, wires)
    The single qubit Y rotation

    .. math:: R_y(\phi) = e^{-i\phi\sigma_y/2} = \begin{bmatrix}
                \cos(\phi/2) & -\sin(\phi/2) \\
                \sin(\phi/2) & \cos(\phi/2)
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(R_y(\phi)) = \frac{1}{2}\left[f(R_y(\phi+\pi/2)) - f(R_y(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`R_y(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 1
    num_wires = 1
    par_domain = "R"
    grad_method = "A"
    generator = [PauliY, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array([[c, -s], [s, c]])

    def adjoint(self):
        return RY(-self.data[0], wires=self.wires)

    def _controlled(self, wire):
        CRY(*self.parameters, wires=wire + self.wires)


class RZ(DiagonalOperation):
    r"""RZ(phi, wires)
    The single qubit Z rotation

    .. math:: R_z(\phi) = e^{-i\phi\sigma_z/2} = \begin{bmatrix}
                e^{-i\phi/2} & 0 \\
                0 & e^{i\phi/2}
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(R_z(\phi)) = \frac{1}{2}\left[f(R_z(\phi+\pi/2)) - f(R_z(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`R_z(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 1
    num_wires = 1
    par_domain = "R"
    grad_method = "A"
    generator = [PauliZ, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        p = cmath.exp(-0.5j * theta)

        return np.array([[p, 0], [0, p.conjugate()]])

    @classmethod
    def _eigvals(cls, *params):
        theta = params[0]
        p = cmath.exp(-0.5j * theta)

        return np.array([p, p.conjugate()])

    def adjoint(self):
        return RZ(-self.data[0], wires=self.wires)

    def _controlled(self, wire):
        CRZ(*self.parameters, wires=wire + self.wires)


class PhaseShift(DiagonalOperation):
    r"""PhaseShift(phi, wires)
    Arbitrary single qubit local phase shift

    .. math:: R_\phi(\phi) = e^{i\phi/2}R_z(\phi) = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i\phi}
            \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(R_\phi(\phi)) = \frac{1}{2}\left[f(R_\phi(\phi+\pi/2)) - f(R_\phi(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`R_{\phi}(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 1
    num_wires = 1
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[0, 0], [0, 1]]), 1]

    @classmethod
    def _matrix(cls, *params):
        phi = params[0]
        return np.array([[1, 0], [0, cmath.exp(1j * phi)]])

    @classmethod
    def _eigvals(cls, *params):
        phi = params[0]
        return np.array([1, cmath.exp(1j * phi)])

    @staticmethod
    def decomposition(phi, wires):
        decomp_ops = [RZ(phi, wires=wires)]
        return decomp_ops

    def adjoint(self):
        return PhaseShift(-self.data[0], wires=self.wires)

    def _controlled(self, wire):
        ControlledPhaseShift(*self.parameters, wires=wire + self.wires)


class ControlledPhaseShift(DiagonalOperation):
    r"""ControlledPhaseShift(phi, wires)
    A qubit controlled phase shift.

    .. math:: CR_\phi(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0 \\
                0 & 0 & 1 & 0 \\
                0 & 0 & 0 & e^{i\phi}
            \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(CR_\phi(\phi)) = \frac{1}{2}\left[f(CR_\phi(\phi+\pi/2)) - f(CR_\phi(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`CR_{\phi}(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wire the operation acts on
    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 1]]), 1]

    @classmethod
    def _matrix(cls, *params):
        phi = params[0]
        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, cmath.exp(1j * phi)]])

    @classmethod
    def _eigvals(cls, *params):
        phi = params[0]
        return np.array([1, 1, 1, cmath.exp(1j * phi)])

    @staticmethod
    def decomposition(phi, wires):
        decomp_ops = [
            qml.PhaseShift(phi / 2, wires=wires[0]),
            qml.CNOT(wires=[0, 1]),
            qml.PhaseShift(-phi / 2, wires=wires[1]),
            qml.CNOT(wires=[0, 1]),
            qml.PhaseShift(phi / 2, wires=wires[1]),
        ]
        return decomp_ops

    def adjoint(self):
        return ControlledPhaseShift(-self.data[0], wires=self.wires)


class Rot(Operation):
    r"""Rot(phi, theta, omega, wires)
    Arbitrary single qubit rotation

    .. math::

        R(\phi,\theta,\omega) = RZ(\omega)RY(\theta)RZ(\phi)= \begin{bmatrix}
        e^{-i(\phi+\omega)/2}\cos(\theta/2) & -e^{i(\phi-\omega)/2}\sin(\theta/2) \\
        e^{-i(\phi-\omega)/2}\sin(\theta/2) & e^{i(\phi+\omega)/2}\cos(\theta/2)
        \end{bmatrix}.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 3
    * Gradient recipe: :math:`\frac{d}{d\phi}f(R(\phi, \theta, \omega)) = \frac{1}{2}\left[f(R(\phi+\pi/2, \theta, \omega)) - f(R(\phi-\pi/2, \theta, \omega))\right]`
      where :math:`f` is an expectation value depending on :math:`R(\phi, \theta, \omega)`.
      This gradient recipe applies for each angle argument :math:`\{\phi, \theta, \omega\}`.

    .. note::

        If the ``Rot`` gate is not supported on the targeted device, PennyLane
        will attempt to decompose the gate into :class:`~.RZ` and :class:`~.RY` gates.

    Args:
        phi (float): rotation angle :math:`\phi`
        theta (float): rotation angle :math:`\theta`
        omega (float): rotation angle :math:`\omega`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 3
    num_wires = 1
    par_domain = "R"
    grad_method = "A"

    @classmethod
    def _matrix(cls, *params):
        phi, theta, omega = params
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array(
            [
                [cmath.exp(-0.5j * (phi + omega)) * c, -cmath.exp(0.5j * (phi - omega)) * s],
                [cmath.exp(-0.5j * (phi - omega)) * s, cmath.exp(0.5j * (phi + omega)) * c],
            ]
        )

    @staticmethod
    def decomposition(phi, theta, omega, wires):
        decomp_ops = [RZ(phi, wires=wires), RY(theta, wires=wires), RZ(omega, wires=wires)]
        return decomp_ops

    def adjoint(self):
        phi, theta, omega = self.parameters
        return Rot(-omega, -theta, -phi, wires=self.wires)

    def _controlled(self, wire):
        CRot(*self.parameters, wires=wire + self.wires)


class MultiRZ(DiagonalOperation):
    r"""MultiRZ(theta, wires)
    Arbitrary multi Z rotation.

    .. math::

        MultiRZ(\theta) = \exp(-i \frac{\theta}{2} Z^{\otimes n})

    **Details:**

    * Number of wires: Any
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\theta}f(MultiRZ(\theta)) = \frac{1}{2}\left[f(MultiRZ(\theta +\pi/2)) - f(MultiRZ(\theta-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`MultiRZ(\theta)`.

    .. note::

        If the ``MultiRZ`` gate is not supported on the targeted device, PennyLane
        will decompose the gate using :class:`~.RZ` and :class:`~.CNOT` gates.

    Args:
        theta (float): rotation angle :math:`\theta`
        wires (Sequence[int] or int): the wires the operation acts on
    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "R"
    grad_method = "A"

    @classmethod
    def _matrix(cls, theta, n):
        """Matrix representation of a MultiRZ gate.

        Args:
            theta (float): Rotation angle.
            n (int): Number of wires the rotation acts on. This has
                to be given explicitly in the static method as the
                wires object is not available.

        Returns:
            array[complex]: The matrix representation
        """
        multi_Z_rot_eigs = MultiRZ._eigvals(theta, n)
        multi_Z_rot_matrix = np.diag(multi_Z_rot_eigs)

        return multi_Z_rot_matrix

    _generator = None

    @property
    def generator(self):
        if self._generator is None:
            self._generator = [np.diag(pauli_eigs(len(self.wires))), -1 / 2]
        return self._generator

    @property
    def matrix(self):
        # Redefine the property here to pass additionally the number of wires to the ``_matrix`` method
        if self.inverse:
            # The matrix is diagonal, so there is no need to transpose
            return self._matrix(*self.parameters, len(self.wires)).conj()

        return self._matrix(*self.parameters, len(self.wires))

    @classmethod
    def _eigvals(cls, theta, n):
        return np.exp(-1j * theta / 2 * pauli_eigs(n))

    @property
    def eigvals(self):
        # Redefine the property here to pass additionally the number of wires to the ``_eigvals`` method
        if self.inverse:
            return self._eigvals(*self.parameters, len(self.wires)).conj()

        return self._eigvals(*self.parameters, len(self.wires))

    @staticmethod
    @template
    def decomposition(theta, wires):
        for i in range(len(wires) - 1, 0, -1):
            CNOT(wires=[wires[i], wires[i - 1]])

        RZ(theta, wires=wires[0])

        for i in range(len(wires) - 1):
            CNOT(wires=[wires[i + 1], wires[i]])

    def adjoint(self):
        return MultiRZ(-self.parameters[0], wires=self.wires)


class PauliRot(Operation):
    r"""PauliRot(theta, pauli_word, wires)
    Arbitrary Pauli word rotation.

    .. math::

        RP(\theta, P) = \exp(-i \frac{\theta}{2} P)

    **Details:**

    * Number of wires: Any
    * Number of parameters: 2 (1 differentiable parameter)
    * Gradient recipe: :math:`\frac{d}{d\theta}f(RP(\theta)) = \frac{1}{2}\left[f(RP(\theta +\pi/2)) - f(RP(\theta-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`RP(\theta)`.

    .. note::

        If the ``PauliRot`` gate is not supported on the targeted device, PennyLane
        will decompose the gate using :class:`~.RX`, :class:`~.Hadamard`, :class:`~.RZ`
        and :class:`~.CNOT` gates.

    Args:
        theta (float): rotation angle :math:`\theta`
        pauli_word (string): the Pauli word defining the rotation
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 2
    num_wires = AnyWires
    do_check_domain = False
    par_domain = "R"
    grad_method = "A"

    _ALLOWED_CHARACTERS = "IXYZ"

    _PAULI_CONJUGATION_MATRICES = {
        "X": Hadamard._matrix(),
        "Y": RX._matrix(np.pi / 2),
        "Z": np.array([[1, 0], [0, 1]]),
    }

    def __init__(self, *params, wires=None, do_queue=True):
        super().__init__(*params, wires=wires, do_queue=do_queue)

        pauli_word = params[1]

        if not PauliRot._check_pauli_word(pauli_word):
            raise ValueError(
                'The given Pauli word "{}" contains characters that are not allowed.'
                " Allowed characters are I, X, Y and Z".format(pauli_word)
            )

        num_wires = 1 if isinstance(wires, int) else len(wires)

        if not len(pauli_word) == num_wires:
            raise ValueError(
                "The given Pauli word has length {}, length {} was expected for wires {}".format(
                    len(pauli_word), num_wires, wires
                )
            )

    @staticmethod
    def _check_pauli_word(pauli_word):
        """Check that the given Pauli word has correct structure.

        Args:
            pauli_word (str): Pauli word to be checked

        Returns:
            bool: Whether the Pauli word has correct structure.
        """
        return all(pauli in PauliRot._ALLOWED_CHARACTERS for pauli in pauli_word)

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        pauli_word = params[1]

        if not PauliRot._check_pauli_word(pauli_word):
            raise ValueError(
                'The given Pauli word "{}" contains characters that are not allowed.'
                " Allowed characters are I, X, Y and Z".format(pauli_word)
            )

        # Simplest case is if the Pauli is the identity matrix
        if pauli_word == "I" * len(pauli_word):
            return np.exp(-1j * theta / 2) * np.eye(2 ** len(pauli_word))

        # We first generate the matrix excluding the identity parts and expand it afterwards.
        # To this end, we have to store on which wires the non-identity parts act
        non_identity_wires, non_identity_gates = zip(
            *[(wire, gate) for wire, gate in enumerate(pauli_word) if gate != "I"]
        )

        multi_Z_rot_matrix = MultiRZ._matrix(theta, len(non_identity_gates))

        # now we conjugate with Hadamard and RX to create the Pauli string
        conjugation_matrix = functools.reduce(
            np.kron,
            [PauliRot._PAULI_CONJUGATION_MATRICES[gate] for gate in non_identity_gates],
        )

        return expand(
            conjugation_matrix.T.conj() @ multi_Z_rot_matrix @ conjugation_matrix,
            non_identity_wires,
            list(range(len(pauli_word))),
        )

    _generator = None

    @property
    def generator(self):
        if self._generator is None:
            pauli_word = self.parameters[1]

            # Simplest case is if the Pauli is the identity matrix
            if pauli_word == "I" * len(pauli_word):
                self._generator = [np.eye(2 ** len(pauli_word)), -1 / 2]
                return self._generator

            # We first generate the matrix excluding the identity parts and expand it afterwards.
            # To this end, we have to store on which wires the non-identity parts act
            non_identity_wires, non_identity_gates = zip(
                *[(wire, gate) for wire, gate in enumerate(pauli_word) if gate != "I"]
            )

            # get MultiRZ's generator
            multi_Z_rot_generator = np.diag(pauli_eigs(len(non_identity_gates)))

            # now we conjugate with Hadamard and RX to create the Pauli string
            conjugation_matrix = functools.reduce(
                np.kron,
                [PauliRot._PAULI_CONJUGATION_MATRICES[gate] for gate in non_identity_gates],
            )

            self._generator = [
                expand(
                    conjugation_matrix.T.conj() @ multi_Z_rot_generator @ conjugation_matrix,
                    non_identity_wires,
                    list(range(len(pauli_word))),
                ),
                -1 / 2,
            ]

        return self._generator

    @classmethod
    def _eigvals(cls, theta, pauli_word):
        # Identity must be treated specially because its eigenvalues are all the same
        if pauli_word == "I" * len(pauli_word):
            return np.exp(-1j * theta / 2) * np.ones(2 ** len(pauli_word))

        return MultiRZ._eigvals(theta, len(pauli_word))

    @staticmethod
    @template
    def decomposition(theta, pauli_word, wires):
        # Catch cases when the wire is passed as a single int.
        if isinstance(wires, int):
            wires = [wires]

        # Check for identity and do nothing
        if pauli_word == "I" * len(wires):
            return

        active_wires, active_gates = zip(
            *[(wire, gate) for wire, gate in zip(wires, pauli_word) if gate != "I"]
        )

        for wire, gate in zip(active_wires, active_gates):
            if gate == "X":
                Hadamard(wires=[wire])
            elif gate == "Y":
                RX(np.pi / 2, wires=[wire])

        MultiRZ(theta, wires=list(active_wires))

        for wire, gate in zip(active_wires, active_gates):
            if gate == "X":
                Hadamard(wires=[wire])
            elif gate == "Y":
                RX(-np.pi / 2, wires=[wire])

    def adjoint(self):
        return PauliRot(-self.parameters[0], self.parameters[1], wires=self.wires)


# Four term gradient recipe for controlled rotations
c1 = (np.sqrt(2) - 4 * np.cos(np.pi / 8)) / (4 - 8 * np.cos(np.pi / 8))
c2 = (np.sqrt(2) - 1) / (4 * np.cos(np.pi / 8) - 2)
a = np.pi / 2
b = 3 * np.pi / 4
four_term_grad_recipe = ([[c1, 1, a], [-c1, 1, -a], [-c2, 1, b], [c2, 1, -b]],)


class CRX(Operation):
    r"""CRX(phi, wires)
    The controlled-RX operator

    .. math::

        \begin{align}
            CR_x(\phi) &=
            \begin{bmatrix}
            & 1 & 0 & 0 & 0 \\
            & 0 & 1 & 0 & 0\\
            & 0 & 0 & \cos(\phi/2) & -i\sin(\phi/2)\\
            & 0 & 0 & -i\sin(\phi/2) & \cos(\phi/2)
            \end{bmatrix}.
        \end{align}

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(CR_x(\phi)) = \frac{1}{2}\left[f(CR_x(\phi+\pi/2)) - f(CR_x(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`CR_x(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wire the operation acts on
    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    grad_recipe = four_term_grad_recipe

    generator = [np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        js = 1j * math.sin(-theta / 2)

        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, c, js], [0, 0, js, c]])

    @staticmethod
    def decomposition(theta, wires):
        decomp_ops = [
            RZ(np.pi / 2, wires=wires[1]),
            RY(theta / 2, wires=wires[1]),
            CNOT(wires=wires),
            RY(-theta / 2, wires=wires[1]),
            CNOT(wires=wires),
            RZ(-np.pi / 2, wires=wires[1]),
        ]
        return decomp_ops

    def adjoint(self):
        return CRX(-self.data[0], wires=self.wires)


class CRY(Operation):
    r"""CRY(phi, wires)
    The controlled-RY operator

    .. math::

        \begin{align}
            CR_y(\phi) &=
            \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0\\
                0 & 0 & \cos(\phi/2) & -\sin(\phi/2)\\
                0 & 0 & \sin(\phi/2) & \cos(\phi/2)
            \end{bmatrix}.
        \end{align}

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(CR_y(\phi)) = \frac{1}{2}\left[f(CR_y(\phi+\pi/2)) - f(CR_y(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`CR_y(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wire the operation acts on
    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    grad_recipe = four_term_grad_recipe

    generator = [np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, -1j], [0, 0, 1j, 0]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, c, -s], [0, 0, s, c]])

    @staticmethod
    def decomposition(theta, wires):
        decomp_ops = [
            RY(theta / 2, wires=wires[1]),
            CNOT(wires=wires),
            RY(-theta / 2, wires=wires[1]),
            CNOT(wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return CRY(-self.data[0], wires=self.wires)


class CRZ(DiagonalOperation):
    r"""CRZ(phi, wires)
    The controlled-RZ operator

    .. math::

        \begin{align}
             CR_z(\phi) &=
             \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & 1 & 0 & 0\\
                0 & 0 & e^{-i\phi/2} & 0\\
                0 & 0 & 0 & e^{i\phi/2}
            \end{bmatrix}.
        \end{align}


    .. note:: The subscripts of the operations in the formula refer to the wires they act on, e.g. 1 corresponds to the first element in ``wires`` that is the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(CR_z(\phi)) = \frac{1}{2}\left[f(CR_z(\phi+\pi/2)) - f(CR_z(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`CR_z(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wire the operation acts on
    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    grad_recipe = four_term_grad_recipe

    generator = [np.array([[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 1, 0], [0, 0, 0, -1]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        return np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, cmath.exp(-0.5j * theta), 0],
                [0, 0, 0, cmath.exp(0.5j * theta)],
            ]
        )

    @classmethod
    def _eigvals(cls, *params):
        theta = params[0]
        return np.array(
            [
                1,
                1,
                cmath.exp(-0.5j * theta),
                cmath.exp(0.5j * theta),
            ]
        )

    @staticmethod
    def decomposition(lam, wires):
        decomp_ops = [
            PhaseShift(lam / 2, wires=wires[1]),
            CNOT(wires=wires),
            PhaseShift(-lam / 2, wires=wires[1]),
            CNOT(wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        return CRZ(-self.data[0], wires=self.wires)


class CRot(Operation):
    r"""CRot(phi, theta, omega, wires)
    The controlled-Rot operator

    .. math:: CR(\phi, \theta, \omega) = \begin{bmatrix}
            1 & 0 & 0 & 0 \\
            0 & 1 & 0 & 0\\
            0 & 0 & e^{-i(\phi+\omega)/2}\cos(\theta/2) & -e^{i(\phi-\omega)/2}\sin(\theta/2)\\
            0 & 0 & e^{-i(\phi-\omega)/2}\sin(\theta/2) & e^{i(\phi+\omega)/2}\cos(\theta/2)
        \end{bmatrix}.

    .. note:: The first wire provided corresponds to the **control qubit**.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 3
    * Gradient recipe: :math:`\frac{d}{d\phi}f(CR(\phi, \theta, \omega)) = \frac{1}{2}\left[f(CR(\phi+\pi/2, \theta, \omega)) - f(CR(\phi-\pi/2, \theta, \omega))\right]`
      where :math:`f` is an expectation value depending on :math:`CR(\phi, \theta, \omega)`.
      This gradient recipe applies for each angle argument :math:`\{\phi, \theta, \omega\}`.

    Args:
        phi (float): rotation angle :math:`\phi`
        theta (float): rotation angle :math:`\theta`
        omega (float): rotation angle :math:`\omega`
        wires (Sequence[int]): the wire the operation acts on
    """
    num_params = 3
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    grad_recipe = four_term_grad_recipe * 3

    @classmethod
    def _matrix(cls, *params):
        phi, theta, omega = params
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array(
            [
                [1, 0, 0, 0],
                [0, 1, 0, 0],
                [0, 0, cmath.exp(-0.5j * (phi + omega)) * c, -cmath.exp(0.5j * (phi - omega)) * s],
                [0, 0, cmath.exp(-0.5j * (phi - omega)) * s, cmath.exp(0.5j * (phi + omega)) * c],
            ]
        )

    @staticmethod
    def decomposition(phi, theta, omega, wires):
        decomp_ops = [
            RZ((phi - omega) / 2, wires=wires[1]),
            CNOT(wires=wires),
            RZ(-(phi + omega) / 2, wires=wires[1]),
            RY(-theta / 2, wires=wires[1]),
            CNOT(wires=wires),
            RY(theta / 2, wires=wires[1]),
            RZ(omega, wires=wires[1]),
        ]
        return decomp_ops

    def adjoint(self):
        phi, theta, omega = self.parameters
        return CRot(-omega, -theta, -phi, wires=self.wires)


class U1(Operation):
    r"""U1(phi)
    U1 gate.

    .. math:: U_1(\phi) = e^{i\phi/2}R_z(\phi) = \begin{bmatrix}
                1 & 0 \\
                0 & e^{i\phi}
            \end{bmatrix}.

    .. note::

        The ``U1`` gate is an alias for the phase shift operation :class:`~.PhaseShift`.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_1(\phi)) = \frac{1}{2}\left[f(U_1(\phi+\pi/2)) - f(U_1(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`U_1(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wire the operation acts on
    """
    num_params = 1
    num_wires = 1
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[0, 0], [0, 1]]), 1]

    @classmethod
    def _matrix(cls, *params):
        phi = params[0]
        return np.array([[1, 0], [0, cmath.exp(1j * phi)]])

    @staticmethod
    def decomposition(phi, wires):
        return [PhaseShift(phi, wires=wires)]

    def adjoint(self):
        return U1(-self.data[0], wires=self.wires)


class U2(Operation):
    r"""U2(phi, lambda, wires)
    U2 gate.

    .. math::

        U_2(\phi, \lambda) = \frac{1}{\sqrt{2}}\begin{bmatrix} 1 & -\exp(i \lambda)
        \\ \exp(i \phi) & \exp(i (\phi + \lambda)) \end{bmatrix}

    The :math:`U_2` gate is related to the single-qubit rotation :math:`R` (:class:`Rot`) and the
    :math:`R_\phi` (:class:`PhaseShift`) gates via the following relation:

    .. math::

        U_2(\phi, \lambda) = R_\phi(\phi+\lambda) R(\lambda,\pi/2,-\lambda)

    .. note::

        If the ``U2`` gate is not supported on the targeted device, PennyLane
        will attempt to decompose the gate into :class:`~.Rot` and :class:`~.PhaseShift` gates.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 2
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_2(\phi, \lambda)) = \frac{1}{2}\left[f(U_2(\phi+\pi/2, \lambda)) - f(U_2(\phi-\pi/2, \lambda))\right]`
      where :math:`f` is an expectation value depending on :math:`U_2(\phi, \lambda)`.
      This gradient recipe applies for each angle argument :math:`\{\phi, \lambda\}`.

    Args:
        phi (float): azimuthal angle :math:`\phi`
        lambda (float): quantum phase :math:`\lambda`
        wires (Sequence[int] or int): the subsystem the gate acts on
    """
    num_params = 2
    num_wires = 1
    par_domain = "R"
    grad_method = "A"

    @classmethod
    def _matrix(cls, *params):
        phi, lam = params
        return INV_SQRT2 * np.array(
            [[1, -cmath.exp(1j * lam)], [cmath.exp(1j * phi), cmath.exp(1j * (phi + lam))]]
        )

    @staticmethod
    def decomposition(phi, lam, wires):
        decomp_ops = [
            Rot(lam, np.pi / 2, -lam, wires=wires),
            PhaseShift(lam, wires=wires),
            PhaseShift(phi, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        phi, lam = self.parameters
        new_lam = (np.pi - phi) % (2 * np.pi)
        new_phi = (np.pi - lam) % (2 * np.pi)
        return U2(new_phi, new_lam, wires=self.wires)


class U3(Operation):
    r"""U3(theta, phi, lambda, wires)
    Arbitrary single qubit unitary.

    .. math::

        U_3(\theta, \phi, \lambda) = \begin{bmatrix} \cos(\theta/2) & -\exp(i \lambda)\sin(\theta/2) \\
        \exp(i \phi)\sin(\theta/2) & \exp(i (\phi + \lambda))\cos(\theta/2) \end{bmatrix}

    The :math:`U_3` gate is related to the single-qubit rotation :math:`R` (:class:`Rot`) and the
    :math:`R_\phi` (:class:`PhaseShift`) gates via the following relation:

    .. math::

        U_3(\theta, \phi, \lambda) = R_\phi(\phi+\lambda) R(\lambda,\theta,-\lambda)

    .. note::

        If the ``U3`` gate is not supported on the targeted device, PennyLane
        will attempt to decompose the gate into :class:`~.PhaseShift` and :class:`~.Rot` gates.

    **Details:**

    * Number of wires: 1
    * Number of parameters: 3
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_3(\theta, \phi, \lambda)) = \frac{1}{2}\left[f(U_3(\theta+\pi/2, \phi, \lambda)) - f(U_3(\theta-\pi/2, \phi, \lambda))\right]`
      where :math:`f` is an expectation value depending on :math:`U_3(\theta, \phi, \lambda)`.
      This gradient recipe applies for each angle argument :math:`\{\theta, \phi, \lambda\}`.

    Args:
        theta (float): polar angle :math:`\theta`
        phi (float): azimuthal angle :math:`\phi`
        lambda (float): quantum phase :math:`\lambda`
        wires (Sequence[int] or int): the subsystem the gate acts on
    """
    num_params = 3
    num_wires = 1
    par_domain = "R"
    grad_method = "A"

    @classmethod
    def _matrix(cls, *params):
        theta, phi, lam = params
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array(
            [
                [c, -s * cmath.exp(1j * lam)],
                [s * cmath.exp(1j * phi), c * cmath.exp(1j * (phi + lam))],
            ]
        )

    @staticmethod
    def decomposition(theta, phi, lam, wires):
        decomp_ops = [
            Rot(lam, theta, -lam, wires=wires),
            PhaseShift(lam, wires=wires),
            PhaseShift(phi, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        theta, phi, lam = self.parameters
        new_lam = (np.pi - phi) % (2 * np.pi)
        new_phi = (np.pi - lam) % (2 * np.pi)
        return U3(theta, new_phi, new_lam, wires=self.wires)


# =============================================================================
# Quantum chemistry
# =============================================================================


class SingleExcitation(Operation):
    r"""SingleExcitation(phi, wires)
    Single excitation rotation.

    .. math:: U(\phi) = \begin{bmatrix}
                1 & 0 & 0 & 0 \\
                0 & \cos(\phi/2) & -\sin(\phi/2) & 0 \\
                0 & \sin(\phi/2) & \cos(\phi/2) & 0 \\
                0 & 0 & 0 & 1
            \end{bmatrix}.

    This operation performs a rotation in the two-dimensional subspace :math:`\{|01\rangle,
    |10\rangle\}`. The name originates from the occupation-number representation of
    fermionic wavefunctions, where the transformation  from :math:`|10\rangle` to :math:`|01\rangle`
    is interpreted as "exciting" a particle from the first qubit to the second.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: Obtained from its decomposition in terms of the
      :class:`~.SingleExcitationPlus` and :class:`~.SingleExcitationMinus` operations

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wires the operation acts on


    **Example**

    The following circuit performs the transformation :math:`|10\rangle\rightarrow \cos(
    \phi/2)|10\rangle -\sin(\phi/2)|01\rangle`:

    .. code-block::

        @qml.qnode(dev)
        def circuit(phi):
            qml.PauliX(wires=0)
            qml.SingleExcitation(phi, wires=[0, 1])
    """

    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[0, 0, 0, 0], [0, 0, -1j, 0], [0, 1j, 0, 0], [0, 0, 0, 0]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]])

    @staticmethod
    def decomposition(theta, wires):
        decomp_ops = [
            SingleExcitationPlus(theta / 2, wires=wires),
            SingleExcitationMinus(theta / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        (phi,) = self.parameters
        return SingleExcitation(-phi, wires=self.wires)


class SingleExcitationMinus(Operation):
    r"""SingleExcitationMinus(phi, wires)
    Single excitation rotation with negative phase-shift outside the rotation subspace.

    .. math:: U_-(\phi) = \begin{bmatrix}
                e^{-i\phi/2} & 0 & 0 & 0 \\
                0 & \cos(\phi/2) & -\sin(\phi/2) & 0 \\
                0 & \sin(\phi/2) & \cos(\phi/2) & 0 \\
                0 & 0 & 0 & e^{-i\phi/2}
            \end{bmatrix}.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_-(\phi)) = \frac{1}{2}\left[f(U_-(\phi+\pi/2)) - f(U_-(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`U_-(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wires the operation acts on

    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[1, 0, 0, 0], [0, 0, -1j, 0], [0, 1j, 0, 0], [0, 0, 0, 1]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        e = cmath.exp(-1j * theta / 2)

        return np.array([[e, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, e]])

    def adjoint(self):
        (phi,) = self.parameters
        return SingleExcitationMinus(-phi, wires=self.wires)


class SingleExcitationPlus(Operation):
    r"""SingleExcitationPlus(phi, wires)
    Single excitation rotation with positive phase-shift outside the rotation subspace.

    .. math:: U_+(\phi) = \begin{bmatrix}
                e^{i\phi/2} & 0 & 0 & 0 \\
                0 & \cos(\phi/2) & -\sin(\phi/2) & 0 \\
                0 & \sin(\phi/2) & \cos(\phi/2) & 0 \\
                0 & 0 & 0 & e^{i\phi/2}
            \end{bmatrix}.

    **Details:**

    * Number of wires: 2
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_+(\phi)) = \frac{1}{2}\left[f(U_+(\phi+\pi/2)) - f(U_+(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`U_+(\phi)`.

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int] or int): the wires the operation acts on

    """
    num_params = 1
    num_wires = 2
    par_domain = "R"
    grad_method = "A"
    generator = [np.array([[-1, 0, 0, 0], [0, 0, -1j, 0], [0, 1j, 0, 0], [0, 0, 0, -1]]), -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        e = cmath.exp(1j * theta / 2)

        return np.array([[e, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, e]])

    def adjoint(self):
        (phi,) = self.parameters
        return SingleExcitationPlus(-phi, wires=self.wires)


# =============================================================================
# Arbitrary operations
# =============================================================================


class QubitUnitary(Operation):
    r"""QubitUnitary(U, wires)
    Apply an arbitrary fixed unitary matrix.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None

    Args:
        U (array[complex]): square unitary matrix
        wires (Sequence[int] or int): the wire(s) the operation acts on
    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    @classmethod
    def _matrix(cls, *params):
        U = np.asarray(params[0])

        if U.ndim != 2 or U.shape[0] != U.shape[1]:
            raise ValueError("Operator must be a square matrix.")

        if not np.allclose(U @ U.conj().T, np.identity(U.shape[0])):
            raise ValueError("Operator must be unitary.")

        return U

    def adjoint(self):
        return QubitUnitary(qml.math.T(qml.math.conj(self.data[0])), wires=self.wires)

    def _controlled(self, wire):
        ControlledQubitUnitary(*self.parameters, control_wires=wire, wires=self.wires)


class ControlledQubitUnitary(QubitUnitary):
    r"""ControlledQubitUnitary(U, control_wires, wires, control_values)
    Apply an arbitrary fixed unitary to ``wires`` with control from the ``control_wires``.

    In addition to default ``Operation`` instance attributes, the following are
    available for ``ControlledQubitUnitary``:

    * ``control_wires``: wires that act as control for the operation
    * ``U``: unitary applied to the target wires

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None

    Args:
        U (array[complex]): square unitary matrix
        control_wires (Union[Wires, Sequence[int], or int]): the control wire(s)
        wires (Union[Wires, Sequence[int], or int]): the wire(s) the unitary acts on
        control_values (str): a string of bits representing the state of the control
            qubits to control on (default is the all 1s state)

    **Example**

    The following shows how a single-qubit unitary can be applied to wire ``2`` with control on
    both wires ``0`` and ``1``:

    >>> U = np.array([[ 0.94877869,  0.31594146], [-0.31594146,  0.94877869]])
    >>> qml.ControlledQubitUnitary(U, control_wires=[0, 1], wires=2)

    Typically controlled operations apply a desired gate if the control qubits
    are all in the state :math:`\vert 1\rangle`. However, there are some situations where
    it is necessary to apply a gate conditioned on all qubits being in the
    :math:`\vert 0\rangle` state, or a mix of the two.

    The state on which to control can be changed by passing a string of bits to
    `control_values`. For example, if we want to apply a single-qubit unitary to
    wire ``3`` conditioned on three wires where the first is in state ``0``, the
    second is in state ``1``, and the third in state ``1``, we can write:

    >>> qml.ControlledQubitUnitary(U, control_wires=[0, 1, 2], wires=3, control_values='011')

    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    def __init__(self, *params, control_wires=None, wires=None, control_values=None, do_queue=True):
        if control_wires is None:
            raise ValueError("Must specify control wires")

        wires = Wires(wires)
        control_wires = Wires(control_wires)

        if Wires.shared_wires([wires, control_wires]):
            raise ValueError(
                "The control wires must be different from the wires specified to apply the unitary on."
            )

        U = params[0]
        target_dim = 2 ** len(wires)
        if len(U) != target_dim:
            raise ValueError(f"Input unitary must be of shape {(target_dim, target_dim)}")

        # Saving for the circuit drawer
        self.control_wires = control_wires
        self.U = U

        wires = control_wires + wires

        # If control values unspecified, we control on the all-ones string
        if not control_values:
            control_values = "1" * len(control_wires)

        control_int = self._parse_control_values(control_wires, control_values)

        # A multi-controlled operation is a block-diagonal matrix partitioned into
        # blocks where the operation being applied sits in the block positioned at
        # the integer value of the control string. For example, controlling a
        # unitary U with 2 qubits will produce matrices with block structure
        # (U, I, I, I) if the control is on bits '00', (I, U, I, I) if on bits '01',
        # etc. The positioning of the block is controlled by padding the block diagonal
        # to the left and right with the correct amount of identity blocks.

        padding_left = control_int * len(U)
        padding_right = 2 ** len(wires) - len(U) - padding_left

        CU = block_diag(np.eye(padding_left), U, np.eye(padding_right))

        params = list(params)
        params[0] = CU

        super().__init__(*params, wires=wires, do_queue=do_queue)

    @staticmethod
    def _parse_control_values(control_wires, control_values):
        """Ensure any user-specified control strings have the right format."""
        if isinstance(control_values, str):
            if len(control_values) != len(control_wires):
                raise ValueError("Length of control bit string must equal number of control wires.")

            # Make sure all values are either 0 or 1
            if any(x not in ["0", "1"] for x in control_values):
                raise ValueError("String of control values can contain only '0' or '1'.")

            control_int = int(control_values, 2)
        else:
            raise ValueError("Alternative control values must be passed as a binary string.")

        return control_int

    def _controlled(self, wire):
        ControlledQubitUnitary(*self.parameters, control_wires=wire, wires=self.wires)


class MultiControlledX(ControlledQubitUnitary):
    r"""MultiControlledX(control_wires, wires, control_values)
    Apply a Pauli X gate controlled on an arbitrary computational basis state.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None

    Args:
        control_wires (Union[Wires, Sequence[int], or int]): the control wire(s)
        wires (Union[Wires or int]): a single target wire the operation acts on
        control_values (str): a string of bits representing the state of the control
            qubits to control on (default is the all 1s state)

    **Example**

    The ``MultiControlledX`` operation (sometimes called a mixed-polarity
    multi-controlled Toffoli) is a commonly-encountered case of the
    :class:`~.pennylane.ControlledQubitUnitary` operation wherein the applied
    unitary is the Pauli X (NOT) gate. It can be used in the same manner as
    ``ControlledQubitUnitary``, but there is no need to specify a matrix
    argument:

    >>> qml.MultiControlledX(control_wires=[0, 1, 2, 3], wires=4, control_values='1110'])

    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    def __init__(self, control_wires=None, wires=None, control_values=None, do_queue=True):
        if len(Wires(wires)) != 1:
            raise ValueError("MultiControlledX accepts a single target wire.")

        super().__init__(
            np.array([[0, 1], [1, 0]]),
            control_wires=control_wires,
            wires=wires,
            control_values=control_values,
            do_queue=do_queue,
        )


class DiagonalQubitUnitary(DiagonalOperation):
    r"""DiagonalQubitUnitary(D, wires)
    Apply an arbitrary fixed diagonal unitary matrix.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None

    Args:
        D (array[complex]): diagonal of unitary matrix
        wires (Sequence[int] or int): the wire(s) the operation acts on
    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    @classmethod
    def _eigvals(cls, *params):
        D = np.asarray(params[0])

        if not np.allclose(D * D.conj(), np.ones_like(D)):
            raise ValueError("Operator must be unitary.")

        return D

    @staticmethod
    def decomposition(D, wires):
        return [QubitUnitary(np.diag(D), wires=wires)]

    def adjoint(self):
        return DiagonalQubitUnitary(qml.math.conj(self.parameters[0]), wires=self.wires)

    def _controlled(self, control):
        DiagonalQubitUnitary(
            qml.math.concatenate([np.array([1, 1]), self.parameters[0]]),
            wires=Wires(control) + self.wires,
        )


class QFT(Operation):
    r"""QFT(wires)
    Apply a quantum Fourier transform (QFT).

    For the :math:`N`-qubit computational basis state :math:`|m\rangle`, the QFT performs the
    transformation

    .. math::

        |m\rangle \rightarrow \frac{1}{\sqrt{2^{N}}}\sum_{n=0}^{2^{N} - 1}\omega_{N}^{mn} |n\rangle,

    where :math:`\omega_{N} = e^{\frac{2 \pi i}{2^{N}}}` is the :math:`2^{N}`-th root of unity.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 0
    * Gradient recipe: None

    Args:
        wires (int or Iterable[Number, str]]): the wire(s) the operation acts on

    **Example**

    The quantum Fourier transform is applied by specifying the corresponding wires:

    .. code-block::

        wires = 3

        @qml.qnode(dev)
        def circuit_qft(basis_state):
            qml.BasisState(basis_state, wires=range(wires))
            qml.QFT(wires=range(wires))
            return qml.state()

    """
    num_params = 0
    num_wires = AnyWires
    par_domain = None
    grad_method = None

    @property
    def matrix(self):
        # Redefine the property here to allow for a custom _matrix signature
        mat = self._matrix(len(self.wires))
        if self.inverse:
            mat = mat.conj()
        return mat

    @classmethod
    @functools.lru_cache()
    def _matrix(cls, num_wires):
        dimension = 2 ** num_wires

        mat = np.zeros((dimension, dimension), dtype=np.complex128)
        omega = np.exp(2 * np.pi * 1j / dimension)

        for m in range(dimension):
            for n in range(dimension):
                mat[m, n] = omega ** (m * n)

        return mat / np.sqrt(dimension)

    @staticmethod
    def decomposition(wires):
        num_wires = len(wires)
        shifts = [2 * np.pi * 2 ** -i for i in range(2, num_wires + 1)]

        decomp_ops = []
        for i, wire in enumerate(wires):
            decomp_ops.append(qml.Hadamard(wire))

            for shift, control_wire in zip(shifts[: len(shifts) - i], wires[i + 1 :]):
                op = qml.ControlledPhaseShift(shift, wires=[control_wire, wire])
                decomp_ops.append(op)

        first_half_wires = wires[: num_wires // 2]
        last_half_wires = wires[-(num_wires // 2) :]

        for wire1, wire2 in zip(first_half_wires, reversed(last_half_wires)):
            swap = qml.SWAP(wires=[wire1, wire2])
            decomp_ops.append(swap)

        return decomp_ops


# =============================================================================
# Quantum chemistry
# =============================================================================


class DoubleExcitation(Operation):
    r"""DoubleExcitation(phi, wires)
    Double excitation rotation.

    This operation performs an :math:`SO(2)` rotation in the two-dimensional subspace :math:`\{
    |1100\rangle,|0011\rangle\}`. More precisely, it performs the transformation

    .. math::

        &|0011\rangle \rightarrow \cos(\phi) |0011\rangle - \sin(\phi) |1100\rangle\\
        &|1100\rangle \rightarrow \cos(\phi) |1100\rangle + \sin(\phi) |0011\rangle,

    while leaving all other basis states unchanged.

    The name originates from the occupation-number representation of fermionic wavefunctions, where
    the transformation from :math:`|1100\rangle` to :math:`|0011\rangle` is interpreted as
    "exciting" two particles from the first pair of qubits to the second pair of qubits.

    **Details:**

    * Number of wires: 4
    * Number of parameters: 1
    * Gradient recipe: Obtained from its decomposition in terms of the
      :class:`~.DoubleExcitationPlus` and :class:`~.DoubleExcitationMinus` operations

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wires the operation acts on

    **Example**

    The following circuit performs the transformation :math:`|1100\rangle\rightarrow \cos(
    \phi/2)|1100\rangle -\sin(\phi/2)|0011\rangle)`:

    .. code-block::

        @qml.qnode(dev)
        def circuit(phi):
            qml.PauliX(wires=0)
            qml.PauliX(wires=1)
            qml.DoubleExcitation(phi, wires=[0, 1, 2, 3])
    """

    num_params = 1
    num_wires = 4
    par_domain = "R"
    grad_method = "A"

    G = np.zeros((16, 16), dtype=np.complex64)
    G[3, 12] = -1j  # 3 (dec) = 0011 (bin)
    G[12, 3] = 1j  # 12 (dec) = 1100 (bin)
    generator = [G, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)

        U = np.eye(16)
        U[3, 3] = c  # 3 (dec) = 0011 (bin)
        U[3, 12] = -s  # 12 (dec) = 1100 (bin)
        U[12, 3] = s
        U[12, 12] = c

        return U

    @staticmethod
    def decomposition(theta, wires):
        decomp_ops = [
            DoubleExcitationPlus(theta / 2, wires=wires),
            DoubleExcitationMinus(theta / 2, wires=wires),
        ]
        return decomp_ops

    def adjoint(self):
        (theta,) = self.parameters
        return DoubleExcitation(-theta, wires=self.wires)


class DoubleExcitationPlus(Operation):
    r"""DoubleExcitationPlus(phi, wires)
    Double excitation rotation with positive phase-shift outside the rotation subspace.

    This operation performs an :math:`SO(2)` rotation in the two-dimensional subspace :math:`\{
    |1100\rangle,|0011\rangle\}` while applying a phase-shift on other states. More precisely,
    it performs the transformation

    .. math::

        &|0011\rangle \rightarrow \cos(\phi) |0011\rangle - \sin(\phi) |1100\rangle\\
        &|1100\rangle \rightarrow \cos(\phi) |1100\rangle + \sin(\phi) |0011\rangle\\
        &|x\rangle \rightarrow e^{i\phi} |x\rangle,

    for all other basis states :math:`|x\rangle`.

    **Details:**

    * Number of wires: 4
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_+(\phi)) = \frac{1}{2}\left[f(U_+(\phi+\pi/2)) - f(U_+(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`U_+(\phi)`

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wires the operation acts on
    """

    num_params = 1
    num_wires = 4
    par_domain = "R"
    grad_method = "A"

    G = -1 * np.eye(16, dtype=np.complex64)
    G[3, 3] = 0
    G[12, 12] = 0
    G[3, 12] = -1j  # 3 (dec) = 0011 (bin)
    G[12, 3] = 1j  # 12 (dec) = 1100 (bin)
    generator = [G, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        e = cmath.exp(1j * theta / 2)

        U = e * np.eye(16, dtype=np.complex64)
        U[3, 3] = c  # 3 (dec) = 0011 (bin)
        U[3, 12] = -s  # 12 (dec) = 1100 (bin)
        U[12, 3] = s
        U[12, 12] = c

        return U

    def adjoint(self):
        (theta,) = self.parameters
        return DoubleExcitationPlus(-theta, wires=self.wires)


class DoubleExcitationMinus(Operation):
    r"""DoubleExcitationMinus(phi, wires)
    Double excitation rotation with negative phase-shift outside the rotation subspace.

    This operation performs an :math:`SO(2)` rotation in the two-dimensional subspace :math:`\{
    |1100\rangle,|0011\rangle\}` while applying a phase-shift on other states. More precisely,
    it performs the transformation

    .. math::

        &|0011\rangle \rightarrow \cos(\phi) |0011\rangle - \sin(\phi) |1100\rangle\\
        &|1100\rangle \rightarrow \cos(\phi) |1100\rangle + \sin(\phi) |0011\rangle\\
        &|x\rangle \rightarrow e^{-i\phi} |x\rangle,

    for all other basis states :math:`|x\rangle`.

    **Details:**

    * Number of wires: 4
    * Number of parameters: 1
    * Gradient recipe: :math:`\frac{d}{d\phi}f(U_-(\phi)) = \frac{1}{2}\left[f(U_-(\phi+\pi/2)) - f(U_-(\phi-\pi/2))\right]`
      where :math:`f` is an expectation value depending on :math:`U_-(\phi)`

    Args:
        phi (float): rotation angle :math:`\phi`
        wires (Sequence[int]): the wires the operation acts on
    """

    num_params = 1
    num_wires = 4
    par_domain = "R"
    grad_method = "A"

    G = np.eye(16, dtype=np.complex64)
    G[3, 3] = 0
    G[12, 12] = 0
    G[3, 12] = -1j  # 3 (dec) = 0011 (bin)
    G[12, 3] = 1j  # 12 (dec) = 1100 (bin)
    generator = [G, -1 / 2]

    @classmethod
    def _matrix(cls, *params):
        theta = params[0]
        c = math.cos(theta / 2)
        s = math.sin(theta / 2)
        e = cmath.exp(-1j * theta / 2)

        U = e * np.eye(16, dtype=np.complex64)
        U[3, 3] = c  # 3 (dec) = 0011 (bin)
        U[3, 12] = -s  # 12 (dec) = 1100 (bin)
        U[12, 3] = s
        U[12, 12] = c

        return U

    def adjoint(self):
        (theta,) = self.parameters
        return DoubleExcitationMinus(-theta, wires=self.wires)


# =============================================================================
# State preparation
# =============================================================================


class BasisState(Operation):
    r"""BasisState(n, wires)
    Prepares a single computational basis state.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None (integer parameters not supported)

    .. note::

        If the ``BasisState`` operation is not supported natively on the
        target device, PennyLane will attempt to decompose the operation
        into :class:`~.PauliX` operations.

    Args:
        n (array): prepares the basis state :math:`\ket{n}`, where ``n`` is an
            array of integers from the set :math:`\{0, 1\}`, i.e.,
            if ``n = np.array([0, 1, 0])``, prepares the state :math:`|010\rangle`.
        wires (Sequence[int] or int): the wire(s) the operation acts on
    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    @staticmethod
    def decomposition(n, wires):
        return BasisStatePreparation(n, wires)

    def adjoint(self):
        raise AdjointError("No adjoint exists for BasisState operations.")


class QubitStateVector(Operation):
    r"""QubitStateVector(state, wires)
    Prepare subsystems using the given ket vector in the computational basis.

    **Details:**

    * Number of wires: Any (the operation can act on any number of wires)
    * Number of parameters: 1
    * Gradient recipe: None

    .. note::

        If the ``QubitStateVector`` operation is not supported natively on the
        target device, PennyLane will attempt to decompose the operation
        using the method developed by Möttönen et al. (Quantum Info. Comput.,
        2005).

    Args:
        state (array[complex]): a state vector of size 2**len(wires)
        wires (Sequence[int] or int): the wire(s) the operation acts on
    """
    num_params = 1
    num_wires = AnyWires
    par_domain = "A"
    grad_method = None

    @staticmethod
    def decomposition(state, wires):
        return MottonenStatePreparation(state, wires)

    def adjoint(self):
        raise AdjointError("No adjoint exists for QubitStateVector operations.")


# =============================================================================
# Observables
# =============================================================================


class Hermitian(Observable):
    r"""Hermitian(A, wires)
    An arbitrary Hermitian observable.

    For a Hermitian matrix :math:`A`, the expectation command returns the value

    .. math::
        \braket{A} = \braketT{\psi}{\cdots \otimes I\otimes A\otimes I\cdots}{\psi}

    where :math:`A` acts on the requested wires.

    If acting on :math:`N` wires, then the matrix :math:`A` must be of size
    :math:`2^N\times 2^N`.

    **Details:**

    * Number of wires: Any
    * Number of parameters: 1
    * Gradient recipe: None

    Args:
        A (array): square hermitian matrix
        wires (Sequence[int] or int): the wire(s) the operation acts on
    """
    num_wires = AnyWires
    num_params = 1
    par_domain = "A"
    grad_method = "F"
    _eigs = {}

    @classmethod
    def _matrix(cls, *params):
        A = np.asarray(params[0])

        if A.shape[0] != A.shape[1]:
            raise ValueError("Observable must be a square matrix.")

        if not np.allclose(A, A.conj().T):
            raise ValueError("Observable must be Hermitian.")

        return A

    @property
    def eigendecomposition(self):
        """Return the eigendecomposition of the matrix specified by the Hermitian observable.

        This method uses pre-stored eigenvalues for standard observables where
        possible and stores the corresponding eigenvectors from the eigendecomposition.

        It transforms the input operator according to the wires specified.

        Returns:
            dict[str, array]: dictionary containing the eigenvalues and the eigenvectors of the Hermitian observable
        """
        Hmat = self.matrix
        Hkey = tuple(Hmat.flatten().tolist())
        if Hkey not in Hermitian._eigs:
            w, U = np.linalg.eigh(Hmat)
            Hermitian._eigs[Hkey] = {"eigvec": U, "eigval": w}

        return Hermitian._eigs[Hkey]

    @property
    def eigvals(self):
        """Return the eigenvalues of the specified Hermitian observable.

        This method uses pre-stored eigenvalues for standard observables where
        possible and stores the corresponding eigenvectors from the eigendecomposition.

        Returns:
            array: array containing the eigenvalues of the Hermitian observable
        """
        return self.eigendecomposition["eigval"]

    def diagonalizing_gates(self):
        """Return the gate set that diagonalizes a circuit according to the
        specified Hermitian observable.

        This method uses pre-stored eigenvalues for standard observables where
        possible and stores the corresponding eigenvectors from the eigendecomposition.

        Returns:
            list: list containing the gates diagonalizing the Hermitian observable
        """
        return [QubitUnitary(self.eigendecomposition["eigvec"].conj().T, wires=list(self.wires))]


ops = {
    "Hadamard",
    "PauliX",
    "PauliY",
    "PauliZ",
    "PauliRot",
    "MultiRZ",
    "S",
    "T",
    "SX",
    "CNOT",
    "CZ",
    "CY",
    "SWAP",
    "CSWAP",
    "Toffoli",
    "RX",
    "RY",
    "RZ",
    "PhaseShift",
    "ControlledPhaseShift",
    "Rot",
    "CRX",
    "CRY",
    "CRZ",
    "CRot",
    "U1",
    "U2",
    "U3",
    "BasisState",
    "QubitStateVector",
    "QubitUnitary",
    "ControlledQubitUnitary",
    "MultiControlledX",
    "DiagonalQubitUnitary",
    "QFT",
    "SingleExcitation",
    "SingleExcitationPlus",
    "SingleExcitationMinus",
    "DoubleExcitation",
    "DoubleExcitationPlus",
    "DoubleExcitationMinus",
}


obs = {"Hadamard", "PauliX", "PauliY", "PauliZ", "Hermitian"}


__all__ = list(ops | obs)
