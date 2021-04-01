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
Unit tests for :mod:`fourier` coefficient and spectra calculations.
"""
from functools import partial

import pytest
import pennylane as qml
from pennylane import numpy as np

from pennylane.fourier.coefficients import frequency_spectra, fourier_coefficients


def fourier_function(freq_dict, x):
    """Function to construct and evaluate a Fourier series given
    a dictionary of frequencies and their coefficients.

    Args:
        freq_dict (dict[int, float]): Pairs of positive integer frequencies and corresponding
            Fourier coefficients.

    Returns:
        float: The output of the function \sum(c_n e^{inx}).
    """
    result = 0

    # Handle 0 coefficient separately
    if 0 in freq_dict.keys():
        result = freq_dict[0]

    result += sum(
        [
            coeff * np.exp(1j * freq * x) + np.conj(coeff) * np.exp(-1j * freq * x)
            for freq, coeff in freq_dict.items()
            if freq != 0
        ]
    )
    return result.real


class TestFourierCoefficientSingleVariable:
    """Test that the Fourier coefficients of a single-variable function are computed correctly"""

    @pytest.mark.parametrize(
        "freq_dict,expected_coeffs",
        [
            ({0: 0.5, 1: 2.3, 3: 0.4}, np.array([0.5, 2.3, 0, 0.4, 0.4, 0, 2.3])),
            (
                {3: 0.4, 4: 0.2 + 0.8j, 5: 1j},
                np.array([0, 0, 0, 0.4, 0.2 + 0.8j, 1j, -1j, 0.2 - 0.8j, 0.4, 0.0, 0]),
            ),
        ],
    )
    def test_single_variable_fourier_coeffs(self, freq_dict, expected_coeffs):
        degree = max(freq_dict.keys())
        partial_func = partial(fourier_function, freq_dict)
        coeffs = fourier_coefficients(partial_func, 1, degree)

        assert np.allclose(coeffs, expected_coeffs)


dev_1 = qml.device("default.qubit", wires=1)
dev_2 = qml.device("default.qubit", wires=2)


@qml.qnode(dev_1)
def circuit_one_qubit_one_param_rx(inpt):
    """Circuit with a single-qubit, single-param, output function <Z>.

    By-hand calculation of f(x) gives <Z> = cos^2(x/2) - sin^2(x/2) = cos(x).
    Fourier coeffs are c_1 = c_-1 = 0.5
    """
    qml.RX(inpt[0], wires=0)
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev_1)
def circuit_one_qubit_one_param_h_ry(inpt):
    """Circuit with a single-qubit, single-param, output function <Z>.

    By-hand calculation of f(x) gives <Z> = -sin(x)
    Fourier coeffs are c_1 = 0.5i, c_-1 = -0.5i
    """
    qml.Hadamard(wires=0)
    qml.RY(inpt[0], wires=0)
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev_1)
def circuit_one_qubit_one_param_rx_ry(inpt):
    """Circuit with a single-qubit, single-param, output function <Z>.

    By-hand calculation of f(x) gives <Z> = 1/2 + 1/2 cos(2x)
    Fourier coeffs are c_0 = 0.5, c_1 = c_-1 = 0, c_2 = c_-2 = 0.5
    """
    qml.RX(inpt[0], wires=0)
    qml.RY(inpt[0], wires=0)
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev_1)
def circuit_one_qubit_two_params(inpt):
    """Circuit with a single-qubit, single-param, output function <Z>.

    By-hand calculation of f(x) gives <Z> = cos(x_1) cos(x_2)
    Fourier coeffs are 0.25 for all +/-1 combinations, 0 elsewhere.
    """
    qml.RY(inpt[0], wires=0)
    qml.RX(inpt[1], wires=0)
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev_2)
def circuit_two_qubits_repeated_param(inpt):
    """Circuit with two qubits, repeated single-param output function <Z>

    By-hand calculation of f(x) gives <Z> = 1/2 + 1/2 cos(2x)
    Fourier coeffs are c_0 = 0.5, c_1 = c_-1 = 0, c_2 = c_-2 = 0.5
    (Same as above circuit_one_qubit_one_param_rx_ry, just different qubits).
    """
    qml.RX(inpt[0], wires=0)
    qml.RY(inpt[0], wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev_2)
def circuit_two_qubits_two_params(inpt):
    """Circuit with a single-qubit, two-param output function <Z>.

    By-hand calculation of f(x) gives <Z> = cos(x_1) cos(x_2)
    Fourier coeffs are 0.25 for all +/-1 combinations, 0 elsewhere
    (Same as the circuit with one qubit and two params)
    """
    qml.RY(inpt[0], wires=0)
    qml.RX(inpt[1], wires=1)
    qml.CNOT(wires=[1, 0])
    return qml.expval(qml.PauliZ(0))


class TestFourierCoefficientCircuits:
    """Test calculation of Fourier coefficients for various circuits."""

    @pytest.mark.parametrize(
        "circuit,inpt,degree,expected_coeffs",
        [
            (circuit_one_qubit_one_param_rx, np.array([0.1]), 1, np.array([0, 0.5, 0.5])),
            (circuit_one_qubit_one_param_rx, np.array([0.2]), 2, np.array([0, 0.5, 0, 0, 0.5])),
            (circuit_one_qubit_one_param_h_ry, np.array([-0.6]), 1, np.array([0, 0.5j, -0.5j])),
            (
                circuit_one_qubit_one_param_h_ry,
                np.array([2]),
                3,
                np.array([0, 0.5j, 0, 0, 0, 0, -0.5j]),
            ),
            (
                circuit_one_qubit_one_param_rx_ry,
                np.array([0.02]),
                2,
                np.array([0.5, 0, 0.25, 0.25, 0]),
            ),
            (
                circuit_one_qubit_one_param_rx_ry,
                np.array([1.56]),
                4,
                np.array([0.5, 0, 0.25, 0, 0, 0, 0, 0.25, 0]),
            ),
            (
                circuit_two_qubits_repeated_param,
                np.array([0.5]),
                2,
                np.array([0.5, 0, 0.25, 0.25, 0]),
            ),
            (
                circuit_two_qubits_repeated_param,
                np.array([-0.32]),
                3,
                np.array([0.5, 0, 0.25, 0, 0, 0.25, 0]),
            ),
        ],
    )
    def test_coefficients_one_param_circuits(self, circuit, inpt, degree, expected_coeffs):
        """Test that coeffs for a single instance of a single parameter match the by-hand
        results regardless of input degree (max degree is 1)."""
        coeffs = fourier_coefficients(circuit, len(inpt), degree)
        assert np.allclose(coeffs, expected_coeffs)

    @pytest.mark.parametrize(
        "circuit,inpt,degree,expected_coeffs",
        [
            (
                circuit_two_qubits_two_params,
                np.array([0.1, 0.3]),
                1,
                np.array([[0, 0, 0], [0, 0.25, 0.25], [0, 0.25, 0.25]]),
            ),
            (
                circuit_one_qubit_two_params,
                np.array([-0.25, -0.9]),
                1,
                np.array([[0, 0, 0], [0, 0.25, 0.25], [0, 0.25, 0.25]]),
            ),
        ],
    )
    def test_coefficients_two_param_circuits(self, circuit, inpt, degree, expected_coeffs):
        """Test that coeffs for a single instance of a single parameter match the by-hand
        results regardless of input degree (max degree is 1)."""
        coeffs = fourier_coefficients(circuit, len(inpt), degree)
        assert np.allclose(coeffs, expected_coeffs)


class TestAntiAliasing:
    """Test that anti-aliasing techniques give correct results."""

    @pytest.mark.parametrize(
        "circuit,inpt,degree,expected_coeffs",
        [
            (
                circuit_two_qubits_repeated_param,
                np.array([0.5]),
                1,
                np.array([0.5, 0, 0]),
            ),
        ],
    )
    def test_anti_aliasing_incorrect(self, circuit, inpt, degree, expected_coeffs):
        """Test that anti-aliasing function gives correct results when we ask for
        coefficients below the maximum degree."""
        coeffs_anti_aliased = fourier_coefficients(
            circuit, len(inpt), degree, filter_threshold=degree + 2
        )
        assert np.allclose(coeffs_anti_aliased, expected_coeffs)

        coeffs_regular = fourier_coefficients(circuit, len(inpt), degree, lowpass_filter=False)
        assert not np.allclose(coeffs_regular, expected_coeffs)

    @pytest.mark.parametrize(
        "circuit,inpt,degree",
        [
            (circuit_two_qubits_two_params, np.array([0.1, 0.3]), 1),
            (circuit_one_qubit_two_params, np.array([-0.1, 0.25]), 1),
        ],
    )
    def test_anti_aliasing(self, circuit, inpt, degree):
        """Test that the coefficients obtained through anti-aliasing are the
        same as the ones when we don't anti-alias at the correct degree."""
        coeffs_regular = fourier_coefficients(circuit, len(inpt), degree, lowpass_filter=False)
        coeffs_anti_aliased = fourier_coefficients(circuit, len(inpt), degree)

        assert np.allclose(coeffs_regular, coeffs_anti_aliased)
