# Copyright 2018-2020 Xanadu Quantum Technologies Inc.

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
Pytest configuration file for PennyLane test suite.
"""
import os

import pytest
import numpy as np

import pennylane as qml
from pennylane.devices import DefaultGaussian


# defaults
TOL = 1e-3
TF_TOL = 2e-2
TOL_STOCHASTIC = 0.05


class DummyDevice(DefaultGaussian):
    """Dummy device to allow Kerr operations"""
    _operation_map = DefaultGaussian._operation_map.copy()
    _operation_map['Kerr'] = lambda *x, **y: np.identity(2)


@pytest.fixture(scope="session")
def tol():
    """Numerical tolerance for equality tests."""
    return float(os.environ.get("TOL", TOL))


@pytest.fixture(scope="session")
def tol_stochastic():
    """Numerical tolerance for equality tests of stochastic values."""
    return TOL_STOCHASTIC


@pytest.fixture(scope="session")
def tf_tol():
    """Numerical tolerance for equality tests."""
    return float(os.environ.get("TF_TOL", TF_TOL))


@pytest.fixture(scope="session", params=[1, 2])
def n_layers(request):
    """Number of layers."""
    return request.param


@pytest.fixture(scope="session", params=[2, 3])
def n_subsystems(request):
    """Number of qubits or qumodes."""
    return request.param


@pytest.fixture(scope="session")
def qubit_device(n_subsystems):
    return qml.device('default.qubit', wires=n_subsystems)


@pytest.fixture(scope="function")
def qubit_device_1_wire():
    return qml.device('default.qubit', wires=1)


@pytest.fixture(scope="function")
def qubit_device_2_wires():
    return qml.device('default.qubit', wires=2)


@pytest.fixture(scope="function")
def qubit_device_3_wires():
    return qml.device('default.qubit', wires=3)


@pytest.fixture(scope="session")
def gaussian_device(n_subsystems):
    """Number of qubits or modes."""
    return DummyDevice(wires=n_subsystems)


@pytest.fixture(scope="session")
def gaussian_dummy():
    """Gaussian device with dummy Kerr gate."""
    return DummyDevice


@pytest.fixture(scope="session")
def gaussian_device_2_wires():
    """A 2-mode Gaussian device."""
    return DummyDevice(wires=2)


@pytest.fixture(scope="session")
def gaussian_device_4modes():
    """A 4 mode Gaussian device."""
    return DummyDevice(wires=4)


@pytest.fixture(scope='session')
def torch_support():
    """Boolean fixture for PyTorch support"""
    try:
        import torch
        from torch.autograd import Variable
        torch_support = True
    except ImportError as e:
        torch_support = False

    return torch_support


@pytest.fixture()
def skip_if_no_torch_support(torch_support):
    if not torch_support:
        pytest.skip("Skipped, no torch support")


@pytest.fixture(scope='module')
def tf_support():
    """Boolean fixture for TensorFlow support"""
    try:
        import tensorflow as tf
        tf_support = True

    except ImportError as e:
        tf_support = False

    return tf_support


@pytest.fixture()
def skip_if_no_tf_support(tf_support):
    if not tf_support:
        pytest.skip("Skipped, no tf support")


@pytest.fixture
def skip_if_no_jax_support():
    pytest.importorskip("jax")


@pytest.fixture(scope="module",
                params=[1, 2, 3])
def seed(request):
    """Different seeds."""
    return request.param


@pytest.fixture(scope="function")
def mock_device(monkeypatch):
    """A mock instance of the abstract Device class"""

    with monkeypatch.context() as m:
        dev = qml.Device
        m.setattr(dev, '__abstractmethods__', frozenset())
        m.setattr(dev, 'short_name', 'mock_device')
        m.setattr(dev, 'capabilities', lambda cls: {"model": "qubit"})
        m.setattr(dev, "operations", {"RX", "RY", "RZ", "CNOT", "SWAP"})
        yield qml.Device(wires=2)


@pytest.fixture
def tear_down_hermitian():
    yield None
    qml.Hermitian._eigs = {}

########################### Analytic Circuits ###########################
# The following fixtures return quantum functions and their analytic forms
# Returns:
#    * A quantum function
#    * function computing expected result
#    * function computing expected gradient/ jacobian (None if not applicable)
#    * function computing expected hessian (None if not applicable)

class CircuitFixture():

    def __init__(self):
        self.circuit_func = None
        self.res = None
        self.jac = None
        self.hess = None
        
        self.input_shape = None
        self.output_shape = None

        self.input = None

    

@pytest.fixture(scope="function")
def circuit_basic():
    """ A basic circuit with a single number input and single number output """

    def circuit(x):
        qml.RY(x, wires=0)
        return qml.expval(qml.PauliZ(0))

    def expected_res(x):
        return np.cos(x)

    def expected_grad(x):
        return -np.sin(x)

    def expected_hess(x):
        return -np.cos(x)

    circuit_data = CircuitFixture()
    circuit_data.circuit_func = circuit
    circuit_data.res = expected_res
    circuit_data.jac = expected_grad
    circuit_data.hess = expected_hess

    circuit_data.input_shape = tuple()
    circuit_data.output_shape = tuple()

    circuit_data.input = 1.0

    return circuit_data

@pytest.fixture(scope="function")
def circuit_prob_output():
    """ A circuit taking a single number input and returning the probability """

    def circuit(x):
        qml.RY(x, wires=0)
        return qml.probs(wires=[0])

    def expected_res(x):
        return np.array([np.cos(x/2.0)**2, np.sin(x/2.0)**2])

    def expected_jacobian(x):
        return np.array([-np.sin(x)/2.0, np.sin(x)/2.0])

    def expected_hess(x):
        return np.array([-np.cos(x)/2.0, np.cos(x)/2.0])

    circuit_data = CircuitFixture()
    circuit_data.circuit_func = circuit
    circuit_data.res = expected_res
    circuit_data.jac = expected_grad
    circuit_data.hess = expected_hess

    circuit_data.input_shape = tuple()
    circuit_data.output_shape = (2, )

    circuit_data.input = 1.0

    return circuit_data

@pytest.fixture(scope="function")
def circuit_state_output():
    """A circuit taking a single number input and returning the state """

    def circuit(x):
        qml.RX(x, wires=0)
        return qml.state()

    def expected_res(x):
        return np.array([np.cos(x/2.0), -1j * np.sin(x/2.0)])

    circuit_data = CircuitFixture()
    circuit_data.circuit_func = circuit
    circuit_data.res = expected_res

    circuit_data.input_shape = tuple()
    circuit_data.output_shape = (2, )

    circuit_data.input = 1.0

    return circuit_data

@pytest.fixture(scope="function")
def circuit_vec_input():
    """ A circuit taking an array of length two as input and returning one number"""

    def circuit(x):
        qml.RY(x[0], wires=0)
        qml.RX(x[1], wires=0)
        return qml.expval(qml.PauliZ(0))

    def expected_res(x):
        return np.cos(x[0]) * np.cos(x[1])

    def expected_grad(x):
        return np.array([-np.sin(x[0]) * np.cos(x[1]), -np.cos(x[0]) * np.sin(x[1])])

    def expected_hess(x):
        return np.array([[-np.cos(x[0]) * np.cos(x[1]),  np.sin(x[0]) * np.sin(x[1])],
                         [ np.sin(x[0]) * np.sin(x[1]), -np.cos(x[0]) * np.cos(x[1])]])

    circuit_data = CircuitFixture()
    circuit_data.circuit_func = circuit
    circuit_data.res = expected_res
    circuit_data.jac = expected_grad
    circuit_data.hess = expected_hess

    circuit_data.input_shape = (2,)
    circuit_data.output_shape = tuple()

    circuit_data.input = [1.0, 2.0]

    return circuit_data


    