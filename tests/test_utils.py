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
Unit tests for the :mod:`pennylane.utils` module.
"""
# pylint: disable=no-self-use,too-many-arguments,protected-access
import functools
import itertools
import pytest

import numpy as np

import pennylane as qml
import pennylane.queuing
import pennylane.utils as pu

from pennylane import Identity, PauliX, PauliY, PauliZ
from pennylane.operation import Tensor


flat_dummy_array = np.linspace(-1, 1, 64)
test_shapes = [
    (64,),
    (64, 1),
    (32, 2),
    (16, 4),
    (8, 8),
    (16, 2, 2),
    (8, 2, 2, 2),
    (4, 2, 2, 2, 2),
    (2, 2, 2, 2, 2, 2),
]

# global variables and functions
I = np.identity(2)
X = np.array([[0, 1], [1, 0]])
Y = np.array([[0, -1j], [1j, 0]])
Z = np.array([[1, 0], [0, -1]])


SWAP = np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, 1, 0, 0], [0, 0, 0, 1]])
CNOT = np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]])


U = np.array(
    [
        [0.83645892 - 0.40533293j, -0.20215326 + 0.30850569j],
        [-0.23889780 - 0.28101519j, -0.88031770 - 0.29832709j],
    ]
)

U2 = np.array([[0, 1, 1, 1], [1, 0, 1, -1], [1, -1, 0, 1], [1, 1, -1, 0]]) / np.sqrt(3)


U_toffoli = np.diag([1 for i in range(8)])
U_toffoli[6:8, 6:8] = np.array([[0, 1], [1, 0]])


test_hamiltonians = [
    np.array([[2.5, -0.5], [-0.5, 2.5]]),
    np.array(np.diag([0, 0, 0, 1])),
    np.array([[-2, -2 + 1j, -2, -2], [-2 - 1j, 0, 0, -1], [-2, 0, -2, -1], [-2, -1, -1, 0]]),
]


class TestDecomposition:
    """Tests the decompose_hamiltonian function"""

    @pytest.mark.parametrize("hamiltonian", [np.ones((3, 3)), np.ones((4, 2)), np.ones((2, 4))])
    def test_wrong_shape(self, hamiltonian):
        """Tests that an exception is raised if the Hamiltonian does not have
        the correct shape"""
        with pytest.raises(
            ValueError, match="The Hamiltonian should have shape",
        ):
            pu.decompose_hamiltonian(hamiltonian)

    def test_not_hermitian(self):
        """Tests that an exception is raised if the Hamiltonian is not Hermitian, i.e.
        equal to its own conjugate transpose"""
        with pytest.raises(ValueError, match="The Hamiltonian is not Hermitian"):
            pu.decompose_hamiltonian(np.array([[1, 2], [3, 4]]))

    def test_hide_identity_true(self):
        """Tests that there are no Identity observables in the tensor products
        when hide_identity=True"""
        H = np.array(np.diag([0, 0, 0, 1]))
        coeff, obs_list = pu.decompose_hamiltonian(H, hide_identity=True)
        tensors = filter(lambda obs: isinstance(obs, Tensor), obs_list)

        for tensor in tensors:
            all_identities = all(isinstance(o, Identity) for o in tensor.obs)
            no_identities = not any(isinstance(o, Identity) for o in tensor.obs)
            assert all_identities or no_identities

    @pytest.mark.parametrize("hide_identity", [True, False])
    @pytest.mark.parametrize("hamiltonian", test_hamiltonians)
    def test_observable_types(self, hamiltonian, hide_identity):
        """Tests that the Hamiltonian decomposes into a linear combination of tensors,
        the identity matrix, and Pauli matrices."""
        allowed_obs = (Tensor, Identity, PauliX, PauliY, PauliZ)

        decomposed_coeff, decomposed_obs = pu.decompose_hamiltonian(hamiltonian, hide_identity)
        assert all([isinstance(o, allowed_obs) for o in decomposed_obs])

    @pytest.mark.parametrize("hamiltonian", test_hamiltonians)
    def test_result_length(self, hamiltonian):
        """Tests that tensors are composed of a number of terms equal to the number
        of qubits."""
        decomposed_coeff, decomposed_obs = pu.decompose_hamiltonian(hamiltonian)
        n = int(np.log2(len(hamiltonian)))

        tensors = filter(lambda obs: isinstance(obs, Tensor), decomposed_obs)
        assert all(len(tensor.obs) == n for tensor in tensors)

    @pytest.mark.parametrize("hamiltonian", test_hamiltonians)
    def test_decomposition(self, hamiltonian):
        """Tests that decompose_hamiltonian successfully decomposes Hamiltonians into a
        linear combination of Pauli matrices"""
        decomposed_coeff, decomposed_obs = pu.decompose_hamiltonian(hamiltonian)

        linear_comb = sum([decomposed_coeff[i] * o.matrix for i, o in enumerate(decomposed_obs)])
        assert np.allclose(hamiltonian, linear_comb)


class TestFlatten:
    """Tests the flatten and unflatten functions"""

    @pytest.mark.parametrize("shape", test_shapes)
    def test_flatten(self, shape):
        """Tests that _flatten successfully flattens multidimensional arrays."""

        reshaped = np.reshape(flat_dummy_array, shape)
        flattened = np.array([x for x in pu._flatten(reshaped)])

        assert flattened.shape == flat_dummy_array.shape
        assert np.array_equal(flattened, flat_dummy_array)

    @pytest.mark.parametrize("shape", test_shapes)
    def test_unflatten(self, shape):
        """Tests that _unflatten successfully unflattens multidimensional arrays."""

        reshaped = np.reshape(flat_dummy_array, shape)
        unflattened = np.array([x for x in pu.unflatten(flat_dummy_array, reshaped)])

        assert unflattened.shape == reshaped.shape
        assert np.array_equal(unflattened, reshaped)

    def test_unflatten_error_unsupported_model(self):
        """Tests that unflatten raises an error if the given model is not supported"""

        with pytest.raises(TypeError, match="Unsupported type in the model"):
            model = lambda x: x  # not a valid model for unflatten
            pu.unflatten(flat_dummy_array, model)

    def test_unflatten_error_too_many_elements(self):
        """Tests that unflatten raises an error if the given iterable has
           more elements than the model"""

        reshaped = np.reshape(flat_dummy_array, (16, 2, 2))

        with pytest.raises(ValueError, match="Flattened iterable has more elements than the model"):
            pu.unflatten(np.concatenate([flat_dummy_array, flat_dummy_array]), reshaped)


class TestPauliEigs:
    """Tests for the auxiliary function to return the eigenvalues for Paulis"""

    paulix = np.array([[0, 1], [1, 0]])
    pauliy = np.array([[0, -1j], [1j, 0]])
    pauliz = np.array([[1, 0], [0, -1]])
    hadamard = 1 / np.sqrt(2) * np.array([[1, 1], [1, -1]])

    standard_observables = [paulix, pauliy, pauliz, hadamard]

    matrix_pairs = [
        np.kron(x, y)
        for x, y in list(itertools.product(standard_observables, standard_observables))
    ]

    @pytest.mark.parametrize("pauli", standard_observables)
    def test_correct_eigenvalues_paulis(self, pauli):
        """Test the paulieigs function for one qubit"""
        assert np.array_equal(pu.pauli_eigs(1), np.diag(self.pauliz))

    @pytest.mark.parametrize("pauli_product", matrix_pairs)
    def test_correct_eigenvalues_pauli_kronecker_products_two_qubits(self, pauli_product):
        """Test the paulieigs function for two qubits"""
        assert np.array_equal(pu.pauli_eigs(2), np.diag(np.kron(self.pauliz, self.pauliz)))

    @pytest.mark.parametrize("pauli_product", matrix_pairs)
    def test_correct_eigenvalues_pauli_kronecker_products_three_qubits(self, pauli_product):
        """Test the paulieigs function for three qubits"""
        assert np.array_equal(
            pu.pauli_eigs(3), np.diag(np.kron(self.pauliz, np.kron(self.pauliz, self.pauliz)))
        )

    @pytest.mark.parametrize("depth", list(range(1, 6)))
    def test_cache_usage(self, depth):
        """Test that the right number of cachings have been executed after clearing the cache"""
        pu.pauli_eigs.cache_clear()
        pu.pauli_eigs(depth)
        total_runs = sum([2 ** x for x in range(depth)])
        assert functools._CacheInfo(depth - 1, depth, 128, depth) == pu.pauli_eigs.cache_info()


class TestArgumentHelpers:
    """Tests for auxiliary functions to help with parsing
    Python function arguments"""

    def test_no_default_args(self):
        """Test that empty dict is returned if function has
        no default arguments"""

        def dummy_func(a, b):  # pylint: disable=unused-argument
            pass

        res = pu._get_default_args(dummy_func)
        assert not res

    def test_get_default_args(self):
        """Test that default arguments are correctly extracted"""

        def dummy_func(
            a, b, c=8, d=[0, 0.65], e=np.array([4]), f=None
        ):  # pylint: disable=unused-argument,dangerous-default-value
            pass

        res = pu._get_default_args(dummy_func)
        expected = {"c": (2, 8), "d": (3, [0, 0.65]), "e": (4, np.array([4])), "f": (5, None)}

        assert res == expected

    def test_inv_dict(self):
        """Test _inv_dict correctly inverts a dictionary"""
        test_data = {"c": 8, "d": (0, 0.65), "e": "hi", "f": None, "g": 8}
        res = pu._inv_dict(test_data)
        expected = {8: {"g", "c"}, (0, 0.65): {"d"}, "hi": {"e"}, None: {"f"}}

        assert res == expected

    def test_inv_dict_unhashable_key(self):
        """Test _inv_dict raises an exception if a dictionary value is unhashable"""
        test_data = {"c": 8, "d": [0, 0.65], "e": "hi", "f": None, "g": 8}

        with pytest.raises(TypeError, match="unhashable type"):
            pu._inv_dict(test_data)


class TestExpand:
    """Tests multi-qubit operator expansion"""

    def test_expand_one(self, tol):
        """Test that a 1 qubit gate correctly expands to 3 qubits."""
        # test applied to wire 0
        res = pu.expand(U, [0], 3)
        expected = np.kron(np.kron(U, I), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 1
        res = pu.expand(U, [1], 3)
        expected = np.kron(np.kron(I, U), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 2
        res = pu.expand(U, [2], 3)
        expected = np.kron(np.kron(I, I), U)
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_one_wires_list(self, tol):
        """Test that a 1 qubit gate correctly expands to 3 qubits."""
        # test applied to wire 0
        res = pu.expand(U, [0], [0, 4, 9])
        expected = np.kron(np.kron(U, I), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 4
        res = pu.expand(U, [4], [0, 4, 9])
        expected = np.kron(np.kron(I, U), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 9
        res = pu.expand(U, [9], [0, 4, 9])
        expected = np.kron(np.kron(I, I), U)
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_two_consecutive_wires(self, tol):
        """Test that a 2 qubit gate on consecutive wires correctly
        expands to 4 qubits."""

        # test applied to wire 0+1
        res = pu.expand(U2, [0, 1], 4)
        expected = np.kron(np.kron(U2, I), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 1+2
        res = pu.expand(U2, [1, 2], 4)
        expected = np.kron(np.kron(I, U2), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 2+3
        res = pu.expand(U2, [2, 3], 4)
        expected = np.kron(np.kron(I, I), U2)
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_two_reversed_wires(self, tol):
        """Test that a 2 qubit gate on reversed consecutive wires correctly
        expands to 4 qubits."""

        # CNOT with target on wire 1
        res = pu.expand(CNOT, [1, 0], 4)
        rows = np.array([0, 2, 1, 3])
        expected = np.kron(np.kron(CNOT[:, rows][rows], I), I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_invalid_wires(self):
        """test exception raised if unphysical subsystems provided."""
        with pytest.raises(
            ValueError, match="Invalid target subsystems provided in 'original_wires' argument"
        ):
            pu.expand(U2, [-1, 5], 4)

    def test_expand_invalid_matrix(self):
        """test exception raised if incorrect sized matrix provided/"""
        with pytest.raises(ValueError, match="Matrix parameter must be of size"):
            pu.expand(U, [0, 1], 4)

    def test_expand_three_consecutive_wires(self, tol):
        """Test that a 3 qubit gate on consecutive
        wires correctly expands to 4 qubits."""

        # test applied to wire 0,1,2
        res = pu.expand(U_toffoli, [0, 1, 2], 4)
        expected = np.kron(U_toffoli, I)
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 1,2,3
        res = pu.expand(U_toffoli, [1, 2, 3], 4)
        expected = np.kron(I, U_toffoli)
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_three_nonconsecutive_ascending_wires(self, tol):
        """Test that a 3 qubit gate on non-consecutive but ascending
        wires correctly expands to 4 qubits."""

        # test applied to wire 0,2,3
        res = pu.expand(U_toffoli, [0, 2, 3], 4)
        expected = (
            np.kron(SWAP, np.kron(I, I)) @ np.kron(I, U_toffoli) @ np.kron(SWAP, np.kron(I, I))
        )
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 0,1,3
        res = pu.expand(U_toffoli, [0, 1, 3], 4)
        expected = (
            np.kron(np.kron(I, I), SWAP) @ np.kron(U_toffoli, I) @ np.kron(np.kron(I, I), SWAP)
        )
        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_three_nonconsecutive_nonascending_wires(self, tol):
        """Test that a 3 qubit gate on non-consecutive non-ascending
        wires correctly expands to 4 qubits"""

        # test applied to wire 3, 1, 2
        res = pu.expand(U_toffoli, [3, 1, 2], 4)
        # change the control qubit on the Toffoli gate
        rows = np.array([0, 4, 1, 5, 2, 6, 3, 7])
        expected = np.kron(I, U_toffoli[:, rows][rows])
        assert np.allclose(res, expected, atol=tol, rtol=0)

        # test applied to wire 3, 0, 2
        res = pu.expand(U_toffoli, [3, 0, 2], 4)
        # change the control qubit on the Toffoli gate
        rows = np.array([0, 4, 1, 5, 2, 6, 3, 7])
        expected = (
            np.kron(SWAP, np.kron(I, I))
            @ np.kron(I, U_toffoli[:, rows][rows])
            @ np.kron(SWAP, np.kron(I, I))
        )
        assert np.allclose(res, expected, atol=tol, rtol=0)

    VECTOR1 = np.array([1, -1])
    ONES = np.array([1, 1])

    @pytest.mark.parametrize(
        "original_wires,expanded_wires,expected",
        [
            ([0], 3, np.kron(np.kron(VECTOR1, ONES), ONES)),
            ([1], 3, np.kron(np.kron(ONES, VECTOR1), ONES)),
            ([2], 3, np.kron(np.kron(ONES, ONES), VECTOR1)),
            ([0], [0, 4, 7], np.kron(np.kron(VECTOR1, ONES), ONES)),
            ([4], [0, 4, 7], np.kron(np.kron(ONES, VECTOR1), ONES)),
            ([7], [0, 4, 7], np.kron(np.kron(ONES, ONES), VECTOR1)),
            ([0], [0, 4, 7], np.kron(np.kron(VECTOR1, ONES), ONES)),
            ([4], [4, 0, 7], np.kron(np.kron(VECTOR1, ONES), ONES)),
            ([7], [7, 4, 0], np.kron(np.kron(VECTOR1, ONES), ONES)),
        ],
    )
    def test_expand_vector_single_wire(self, original_wires, expanded_wires, expected, tol):
        """Test that expand_vector works with a single-wire vector."""

        res = pu.expand_vector(TestExpand.VECTOR1, original_wires, expanded_wires)

        assert np.allclose(res, expected, atol=tol, rtol=0)

    VECTOR2 = np.array([1, 2, 3, 4])
    ONES = np.array([1, 1])

    @pytest.mark.parametrize(
        "original_wires,expanded_wires,expected",
        [
            ([0, 1], 3, np.kron(VECTOR2, ONES)),
            ([1, 2], 3, np.kron(ONES, VECTOR2)),
            ([0, 2], 3, np.array([1, 2, 1, 2, 3, 4, 3, 4])),
            ([0, 5], [0, 5, 9], np.kron(VECTOR2, ONES)),
            ([5, 9], [0, 5, 9], np.kron(ONES, VECTOR2)),
            ([0, 9], [0, 5, 9], np.array([1, 2, 1, 2, 3, 4, 3, 4])),
            ([9, 0], [0, 5, 9], np.array([1, 3, 1, 3, 2, 4, 2, 4])),
        ],
    )
    def test_expand_vector_two_wires(self, original_wires, expanded_wires, expected, tol):
        """Test that expand_vector works with a single-wire vector."""

        res = pu.expand_vector(TestExpand.VECTOR2, original_wires, expanded_wires)

        assert np.allclose(res, expected, atol=tol, rtol=0)

    def test_expand_vector_invalid_wires(self):
        """Test exception raised if unphysical subsystems provided."""
        with pytest.raises(
            ValueError, match="Invalid target subsystems provided in 'original_wires' argument"
        ):
            pu.expand_vector(TestExpand.VECTOR2, [-1, 5], 4)

    def test_expand_vector_invalid_vector(self):
        """Test exception raised if incorrect sized vector provided."""
        with pytest.raises(ValueError, match="Vector parameter must be of length"):
            pu.expand_vector(TestExpand.VECTOR1, [0, 1], 4)


@qml.template
def dummy_template(wires):
    """Dummy template for inv tests."""
    for wire in wires:
        qml.RX(1, wires=[wire])
        qml.RY(-1, wires=[wire])


def inverted_dummy_template_operations(wires):
    """The expected inverted operations for the dummy template."""
    ops = []

    for wire in reversed(wires):
        ops.append(qml.RY(-1, wires=[wire]).inv())
        ops.append(qml.RX(1, wires=[wire]).inv())

    return ops


class TestInv:
    """Test the template inversion function."""

    def test_inversion_without_context(self):
        """Test that a sequence of operations is properly inverted."""
        op_queue = [qml.PauliX(0), qml.PauliY(0).inv(), qml.PauliZ(0)]
        inv_queue = [qml.PauliZ(0).inv(), qml.PauliY(0), qml.PauliX(0).inv()]

        inv_ops = pu.inv(op_queue).operations

        for inv_op, exp_op in zip(inv_ops, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_template_inversion_without_context(self):
        """Test that a template is properly inverted."""
        inv_queue = inverted_dummy_template_operations([0, 1, 2])

        inv_ops = pu.inv(dummy_template([0, 1, 2])).operations

        for inv_op, exp_op in zip(inv_ops, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_double_inversion(self):
        """Test that inverting twice changes nothing."""
        op_queue = [qml.PauliX(0), qml.PauliY(0), qml.PauliZ(0)]

        inv_inv_ops = pu.inv(pu.inv(op_queue)).operations

        for inv_inv_op, exp_op in zip(inv_inv_ops, op_queue):
            assert inv_inv_op.name == exp_op.name
            assert inv_inv_op.wires == exp_op.wires
            assert inv_inv_op.data == exp_op.data

    def test_template_double_inversion(self):
        """Test that inverting twice changes nothing for a template."""
        inv_inv_ops = pu.inv(pu.inv(dummy_template([0, 1, 2]))).operations

        for inv_inv_op, exp_op in zip(inv_inv_ops, dummy_template([0, 1, 2])):
            assert inv_inv_op.name == exp_op.name
            assert inv_inv_op.wires == exp_op.wires
            assert inv_inv_op.data == exp_op.data

    def test_inversion_with_context(self):
        """Test that a sequence of operations is properly inverted when a context is present."""
        with pennylane.tape.OperationRecorder() as rec:
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv([qml.RX(1, wires=[0]), qml.RY(2, wires=[0]), qml.RZ(3, wires=[0])])
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RZ(3, wires=[0]).inv(),
            qml.RY(2, wires=[0]).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        for inv_op, exp_op in zip(rec.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_non_queued_inversion_with_context(self):
        """Test that a sequence of operations is properly inverted when a context is present.
        Test that this also works for operations that were not queued."""
        inv_ops = [qml.RX(1, wires=[0]), qml.RY(2, wires=[0]), qml.RZ(3, wires=[0])]

        with pennylane.tape.OperationRecorder() as rec:
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv(inv_ops)
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RZ(3, wires=[0]).inv(),
            qml.RY(2, wires=[0]).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        for inv_op, exp_op in zip(rec.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_mixed_inversion_with_context(self):
        """Test that a sequence of operations is properly inverted when a context is present.
        Test that this also works for operations that were not queued."""
        X0 = qml.PauliX(0)
        Z0 = qml.PauliZ(0)

        with pennylane.tape.OperationRecorder() as rec:
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv([X0, qml.RX(1, wires=[0]), Z0, qml.RY(2, wires=[0])])
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RY(2, wires=[0]).inv(),
            qml.PauliZ(0).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.PauliX(0).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        for inv_op, exp_op in zip(rec.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_mixed_inversion_with_nested_context(self):
        """Test that a sequence of operations is properly inverted when a nested context is present.
        Test that this also works for operations that were not queued."""
        X0 = qml.PauliX(0)
        Z0 = qml.PauliZ(0)

        with pennylane.tape.OperationRecorder() as rec1:
            with pennylane.tape.OperationRecorder() as rec2:
                qml.Hadamard(wires=[0])
                qml.CNOT(wires=[0, 1])
                pu.inv([X0, qml.RX(1, wires=[0]), Z0, qml.RY(2, wires=[0])])
                qml.CNOT(wires=[0, 1])
                qml.Hadamard(wires=[0])

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RY(2, wires=[0]).inv(),
            qml.PauliZ(0).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.PauliX(0).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        for inv_op, exp_op in zip(rec1.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

        for inv_op, exp_op in zip(rec2.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_template_inversion_with_context(self):
        """Test that a template is properly inverted when a context is present."""
        with pennylane.tape.OperationRecorder() as rec:
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv(dummy_template([0, 1, 2]))
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            *inverted_dummy_template_operations([0, 1, 2]),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        for inv_op, exp_op in zip(rec.queue, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_inversion_with_qnode(self):
        """Test that a sequence of operations is properly inverted when inside a QNode."""
        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def qfunc():
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv([qml.RX(1, wires=[0]), qml.RY(2, wires=[0]), qml.RZ(3, wires=[0])])
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

            return qml.expval(qml.PauliZ(0))

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RZ(3, wires=[0]).inv(),
            qml.RY(2, wires=[0]).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        qfunc()

        for inv_op, exp_op in zip(qfunc.qtape.operations, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_non_queued_inversion_with_qnode(self):
        """Test that a sequence of operations is properly inverted inside a QNode.
        Test that this also works for operations that were not queued."""
        inv_ops = [qml.RX(1, wires=[0]), qml.RY(2, wires=[0]), qml.RZ(3, wires=[0])]

        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def qfunc():
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv(inv_ops)
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

            return qml.expval(qml.PauliZ(0))

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RZ(3, wires=[0]).inv(),
            qml.RY(2, wires=[0]).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        qfunc()

        for inv_op, exp_op in zip(qfunc.qtape.operations, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_mixed_inversion_with_qnode(self):
        """Test that a sequence of operations is properly inverted inside a QNode.
        Test that this also works for operations of queued and non-queued operations."""
        X0 = qml.PauliX(0)
        Z0 = qml.PauliZ(0)
        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def qfunc():
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv([X0, qml.RX(1, wires=[0]), Z0, qml.RY(2, wires=[0])])
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

            return qml.expval(qml.PauliZ(0))

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            qml.RY(2, wires=[0]).inv(),
            qml.PauliZ(0).inv(),
            qml.RX(1, wires=[0]).inv(),
            qml.PauliX(0).inv(),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        qfunc()

        for inv_op, exp_op in zip(qfunc.qtape.operations, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_template_inversion_with_qnode(self):
        """Test that a template is properly inverted when inside a QNode."""
        dev = qml.device("default.qubit", wires=2)

        @qml.qnode(dev)
        def qfunc():
            qml.Hadamard(wires=[0])
            qml.CNOT(wires=[0, 1])
            pu.inv(dummy_template([0, 1]))
            qml.CNOT(wires=[0, 1])
            qml.Hadamard(wires=[0])

            return qml.expval(qml.PauliZ(0))

        inv_queue = [
            qml.Hadamard(wires=[0]),
            qml.CNOT(wires=[0, 1]),
            *inverted_dummy_template_operations([0, 1]),
            qml.CNOT(wires=[0, 1]),
            qml.Hadamard(wires=[0]),
        ]

        qfunc()

        for inv_op, exp_op in zip(qfunc.qtape.operations, inv_queue):
            assert inv_op.name == exp_op.name
            assert inv_op.wires == exp_op.wires
            assert inv_op.data == exp_op.data

    def test_argument_wrapping(self):
        """Test that a single operation can be given to inv and is properly inverted."""
        op = qml.PauliX(0)
        exp_op = qml.PauliX(0).inv()

        inv_ops = pu.inv(op).operations

        assert inv_ops[0].name == exp_op.name
        assert inv_ops[0].wires == exp_op.wires
        assert inv_ops[0].data == exp_op.data

    @pytest.mark.parametrize("arg", [2.3, object()])
    def test_argument_type_error(self, arg):
        """Test that the proper error is raised when the argument type is wrong."""
        with pytest.raises(ValueError, match="The provided operation_list is not iterable"):
            pu.inv(arg)

    def test_argument_none_error(self):
        """Test that the proper error is raised when the argument type is wrong."""
        with pytest.raises(
            ValueError,
            match="None was passed as an argument to inv. "
            + "This could happen if inversion of a template without the template decorator is attempted",
        ):
            pu.inv(None)

    def test_callable_argument_error(self):
        """Test that the proper error is raised when the argument is a function."""

        def func(x):
            return x

        with pytest.raises(
            ValueError, match="A function was passed as an argument to inv. ",
        ):
            pu.inv(func)

    @pytest.mark.parametrize("arg", [[1, 2, 3], [qml.PauliX(0), qml.PauliY(1), "Test"], "Test",])
    def test_non_operations_in_list(self, arg):
        """Test that the proper error is raised when the argument does not only contain operations."""
        with pytest.raises(
            ValueError, match="The given operation_list does not only contain Operations"
        ):
            pu.inv(arg)
