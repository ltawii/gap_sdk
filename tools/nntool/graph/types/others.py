# Copyright (C) 2020  GreenWaves Technologies, SAS

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import logging

import numpy as np
from graph.dim import Dim

from utils.symbolic.basic import Abs, Exp, Log, Max, Min, Neg, Pow, Sqrt

from .base import (CanFuseToExpression, ComparableParameters, InsensitiveToQuantization,
                   NoSizeChangeParameters, Parameters, SensitiveToOrder,
                   SingleInputAndOutput, Transposable, expression_op)

LOG = logging.getLogger("nntool." + __name__)


class TransposeParameters(Transposable, SingleInputAndOutput, InsensitiveToQuantization):
    op_name = "transpose"

    def __init__(self, *args, transpose=None, **kwargs):
        super(TransposeParameters, self).__init__(*args, **kwargs)
        self.transpose_in = [transpose]

    def get_parameter_size(self):
        return 0

    def permute(self, val):
        return [val[i] for i in self.transpose_in[0]]

    def does_nothing(self):
        def not_one(x):
            return x != 1
        return list(
            filter(not_one, self.in_dims[0].shape)) == list(
                filter(not_one, self.permute(self.in_dims[0].shape)))

    @property
    def can_equalize(self):
        return False

    def real_shape(self):
        input_shape = self.in_dims[0].shape
        cond_input_idx = [i for i, sz in enumerate(
            self.in_dims[0].shape) if sz != 1]
        real_transpose = [
            i for i in self.transpose_in[0] if i in cond_input_idx]
        cond_input_shape = [input_shape[i] for i in cond_input_idx]
        cond_transpose = [cond_input_idx.index(i) for i in real_transpose]
        return tuple(cond_input_shape), tuple(cond_transpose)

    @property
    def transpose_dimension(self):
        if self._transpose_in is None:
            return 1
        return len(self.transpose_in[0])

    @property
    def transpose_out(self):
        return None

    @transpose_out.setter
    def transpose_out(self, val):
        self._transpose_in = val

    def get_output_size(self, in_dims):
        self.in_dims = self.clone_dim_with_hints(in_dims)
        out_dim = in_dims[0].clone()
        if self.transpose_in:
            out_dim = out_dim.transpose(self.transpose_in[0])
        return [out_dim]

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "T {} {}".format(
            self.transpose_in and ','.join(
                [str(i) for i in self.transpose_in[0]]) or "None",
            self.at_options
        )


class CopyParameters(Parameters, InsensitiveToQuantization):
    op_name = "copy"

    def __init__(self, *args, **kwargs):
        super(CopyParameters, self).__init__(*args, **kwargs)

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def get_output_size(self, in_dims):
        return [in_dims[0].clone()]

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return ""

class QuantizeParameters(Parameters):
    op_name = "quantize"

    def __init__(self, *args, from_qtype=None, to_qtype=None, **kwargs):
        super(QuantizeParameters, self).__init__(*args, **kwargs)
        self.from_qtype = from_qtype
        self.to_qtype = to_qtype

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def get_output_size(self, in_dims):
        return [in_dims[0].clone()]

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return ""

class ReverseParameters(Parameters, InsensitiveToQuantization):
    op_name = "reverse"

    def __init__(self, *args, axis=0, **kwargs):
        super(ReverseParameters, self).__init__(*args, **kwargs)
        self.axis = axis

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def get_output_size(self, in_dims):
        return [in_dims[0].clone()]

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "A {}".format(self.axis)


class ConcatParameters(Transposable):
    op_name = "concat"

    def __init__(self, *args, axis=None, axis_hint=None, **kwargs):
        super(ConcatParameters, self).__init__(*args, **kwargs)
        self._axis = axis
        self._axis_hint = axis_hint

    @property
    def axis(self):
        return self._axis

    @axis.setter
    def axis(self, val):
        self._axis = val

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def get_output_size(self, in_dims):
        self.in_dims = self.clone_dim_with_hints(in_dims)
        if self.transpose_in:
            in_dims = [(in_dim.clone() if self.transpose_in[idx] is None
                        else in_dim.clone().transpose(self.transpose_in[idx]))
                       for idx, in_dim in enumerate(in_dims)]
        if in_dims[0].is_named and self._axis_hint:
            self._axis = in_dims[0].get_order_idx(self._axis_hint)
        out_dim = Dim.combine([in_dim for in_dim in in_dims], self.axis)
        if self.transpose_out:
            out_dim.transpose(self.transpose_out[0])
        return [out_dim]

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "A {} {} {}".format(
            self.axis,
            Transposable.__str__(self),
            self.at_options
        )


class SplitParameters(Transposable):
    op_name = "split"

    def __init__(self, *args,
                 act_slices=None,
                 out_shapes=None,
                 axis=None,
                 **kwargs):

        super(SplitParameters, self).__init__(*args, **kwargs)
        self.act_slices = act_slices
        self.out_shapes = out_shapes
        self.axis = axis

    def numpy_split(self, arr: np.ndarray):
        slice_specs = [tuple([slice(elem[0], elem[1], elem[2])
                              for elem in act_slice])
                       for act_slice in self.act_slices]
        return [arr[spec] for spec in slice_specs]

    @staticmethod
    def get_splits(in_shape, axis, splits=None, num_splits=None):
        assert splits or num_splits, "no split parameters provided"
        assert in_shape[axis] is not None, "split on undefined axis"
        in_idx = 0
        act_slices = []
        out_shapes = []
        if splits:
            for sz in splits:
                act_slices.append([(in_idx, in_idx + sz, 1) if idx == axis else (0, shape, 1)
                                   for idx, shape in enumerate(in_shape)
                                   if shape is not None])
                out_shapes.append([sz if shape is not None and idx == axis else shape
                                   for idx, shape in enumerate(in_shape)])
                in_idx += sz
        elif num_splits:
            assert in_shape[axis] % num_splits == 0, "dimension of split is not divisible by number of splits"
            sz = in_shape[axis] // num_splits
            while in_idx < in_shape[axis]:
                act_slices.append([(in_idx, in_idx + sz, 1) if idx == axis else (0, shape, 1)
                                   for idx, shape in enumerate(in_shape)
                                   if shape is not None])
                out_shapes.append([sz if shape is not None and idx == axis else shape
                                   for idx, shape in enumerate(in_shape)])
                in_idx += sz
        count_nones = sum(1 if dim is None else 0 for dim in in_shape[:axis:])
        axis -= count_nones
        return act_slices, out_shapes, axis

    @property
    def num_splits(self):
        return len(self.act_slices)

    def transpose_params(self, order):
        self.act_slices = [
            [act_slice[idx] for idx in order] for act_slice in self.act_slices
        ]
        self.out_shapes = [
            [shape[idx] for idx in order] for shape in self.out_shapes
        ]

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        out_size = [Dim.unnamed(shape) for shape in self.out_shapes]
        if self.transpose_out:
            out_size = [dim if self.transpose_out[idx] is None else dim.transpose(self.transpose_out[idx])
                        for idx, dim in enumerate(out_size)]
        return out_size

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "A {} {} {}".format(
            self.axis,
            Transposable.__str__(self),
            self.at_options
        )


class GatherParameters(Parameters, SingleInputAndOutput, SensitiveToOrder, InsensitiveToQuantization):
    op_name = "gather"

    def __init__(self, *args,
                 axis=None,
                 indices=None,
                 **kwargs):

        super(GatherParameters, self).__init__(*args, **kwargs)
        self.axis = axis
        self.indices = np.array(indices)

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        in_dim = in_dims[0].clone()
        self.in_dims = [in_dim]
        new_shape = in_dim.shape[:self.axis:] + \
            list(self.indices.shape) + in_dim.shape[self.axis + 1:]
        return [Dim.unnamed(new_shape)]

    @property
    def rank(self):
        return len(self.in_dims[0].shape) + len(self.indices.shape) - 1

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "A %s I %s" % (self.axis, self.indices)


class StridedSliceParameters(Parameters, SingleInputAndOutput, ComparableParameters, InsensitiveToQuantization):

    op_name = "strided_slice"

    def __init__(self, *args,
                 act_slice=None,
                 out_shape=None,
                 **kwargs):

        super(StridedSliceParameters, self).__init__(*args, **kwargs)
        self.act_slice = act_slice
        self.out_shape = out_shape

    def numpy_slice(self, arr: np.ndarray):
        slice_spec = [slice(elem[0], elem[1], elem[2])
                      for elem in self.act_slice if len(elem) == 3]
        return arr[tuple(slice_spec)].reshape(self.out_shape)

    def only_slices_axis(self, axis):
        """check if there is a slice on only one axis"""
        in_shape = self.in_dims[0].shape
        return all(sl[0] == 0 and sl[1] == in_shape[idx] and sl[2] == 1
                   for idx, sl in enumerate(self.act_slice) if idx != axis)

    def is_unit_slice(self, axis):
        """check if the slice on one axis returns shape of 1"""
        slce = self.act_slice[axis]
        if slce[1] > slce[0]:
            return slce[1] - slce[0] == 1 and slce[2] == 1
        else:
            return slce[0] - slce[1] == 2 and slce[2] == -1

    def is_same_operation_as(self, other):
        if not isinstance(other, StridedSliceParameters):
            return False
        if tuple(self.out_shape) != tuple(other.out_shape):
            return False
        if len(self.act_slice) != len(other.act_slice):
            return False
        return all(tuple(elem) == tuple(oelem) for elem, oelem in zip(self.act_slice, other.act_slice))

    @staticmethod
    def get_slice(in_shape, spec, begin_mask, end_mask, ellipsis_mask, new_axis_mask, shrink_axis_mask):
        # reduces the TFLITE specs and masks down to regularized slice list without any
        # elipsises and an output reshape. If only the reshape is necessary returns a boolean
        # indicating this. If can_reshape is true and inshape == outshape then its a noop

        masks = [begin_mask, end_mask, ellipsis_mask, new_axis_mask, shrink_axis_mask]
        act_slice = []
        out_shape = []
        in_idx = 0
        can_reshape = True
        for idx, sz in enumerate(spec):
            mask = [elem & 0x1 for elem in masks]
            masks = [elem >> 1 for elem in masks]
            if in_shape[in_idx] is None:
                in_idx += 1
                continue

            if mask[2]:
                for _ in range(len(in_shape) - (len(spec) - idx) + 1):
                    act_slice.append((0, in_shape[in_idx], 1))
                    out_shape.append(in_shape[in_idx])
                    in_idx += 1
                continue
            if mask[4]:
                if in_shape[in_idx] > 1:
                    can_reshape = False
                if sz[0] < 0:
                    act_idx = in_shape[in_idx] + sz[0]
                else:
                    act_idx = sz[0]
                act_slice.append((act_idx, act_idx + 1, 1))
                in_idx += 1
                continue
            if mask[3]:
                out_shape.append(1)
                continue

            beg = 0 if mask[0] else (
                sz[0] if sz[0] >= 0 else in_shape[in_idx] + sz[0])
            end = in_shape[in_idx] if mask[1] else (
                sz[1] if sz[1] >= 0 else in_shape[in_idx] + sz[1])

            act_slice.append((
                beg,
                end,
                sz[2]
            ))
            out_shape.append((end - beg)//abs(sz[2]))
            if beg != 0 or end != in_shape[in_idx] or sz[2] != 1:
                can_reshape = False
            in_idx += 1
        return act_slice, out_shape, can_reshape

    def only_slices(self, axis):
        return all(dim == self.act_slice[idx][1] and self.act_slice[idx][0] == 0 and self.act_slice[idx][2] == 1
                   for idx, dim in enumerate(self.in_dims[0].shape) if axis != idx)

    @property
    def post_slice_shape(self):
        return [(sl[1] - sl[0])//sl[2] for sl in self.act_slice]

    @property
    def changes_shape(self):
        return len(self.post_slice_shape) > len(self.out_shape)

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        return [Dim.unnamed(self.out_shape)]

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return ",".join("(%s,%s,%s)" % elem for elem in self.act_slice)


class GroupParameters(Parameters, SensitiveToOrder):

    op_name = "group"

    def __init__(self, name, groups, in_dims_hint=None, out_dims_hint=None):

        super(GroupParameters, self).__init__(name,
                                              in_dims_hint=in_dims_hint,
                                              out_dims_hint=out_dims_hint)
        self.groups = groups

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        assert len(in_dims) == 1
        self.in_dims = self.clone_dim_with_hints(in_dims)
        in_dims = self.in_dims[0]
        assert in_dims.c % self.groups == 0
        out_edges = in_dims.c // self.groups
        out_c = in_dims.c // out_edges
        out_dim = in_dims.clone(['c', 'h', 'w'])
        out_dim.c = out_c
        out_dim.impose_order(in_dims.order)
        return [out_dim]

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "GRPS {}".format(
            self.groups
        )


class CastParameters(Parameters, SingleInputAndOutput):
    op_name = "cast"

    def __init__(self, *args, in_dtype=None, out_dtype=None, **kwargs):
        super(CastParameters, self).__init__(*args, **kwargs)
        self.in_dtype = in_dtype
        self.out_dtype = out_dtype

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        assert len(in_dims) == 1
        self.in_dims = self.clone_dim_with_hints(in_dims)
        out_dim = self.in_dims[0].clone()
        return [out_dim]

    @property
    def can_equalize(self):
        return True

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "%s -> %s" % (self.in_dtype, self.out_dtype)


class PadParameters(Parameters, SingleInputAndOutput):
    op_name = "pad"

    def __init__(self, name, padding=None, pad_vals=None, in_dims_hint=None, out_dims_hint=None):

        super(PadParameters, self).__init__(name,
                                            in_dims_hint=in_dims_hint,
                                            out_dims_hint=out_dims_hint)
        self.padding = padding
        self.pad_vals = pad_vals

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        assert len(in_dims) == 1
        self.in_dims = self.clone_dim_with_hints(in_dims)

        out_dim = self.in_dims[0].clone()
        for idx, vals in enumerate(self.padding):
            out_dim[idx] += sum(vals)
        return [out_dim]

    @property
    def can_equalize(self):
        return True

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "PAD {}".format(self.padding)


class UpsampleParameters(Parameters, SingleInputAndOutput, SensitiveToOrder):

    op_name = "upsample"

    def __init__(self, name, algo, factor, in_dims_hint=None, out_dims_hint=None):

        super(UpsampleParameters, self).__init__(name,
                                                 in_dims_hint=in_dims_hint,
                                                 out_dims_hint=out_dims_hint)
        self.algo = algo
        self.factor = factor

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):

        assert len(in_dims) == 1
        self.in_dims = self.clone_dim_with_hints(in_dims)
        in_dims = in_dims[0]

        out_dim = in_dims.clone()
        out_dim = out_dim * self.factor
        out_dim.impose_order(in_dims.order)
        return [out_dim]

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "A {} factor {}".format(
            self.algo,
            self.factor
        )


class BinaryOpParameters(CanFuseToExpression, Parameters):
    op_name = "binary"

    def __new__(cls, *args, op_type="maximum", **kwargs):
        if cls is BinaryOpParameters:
            for subcls in BinaryOpParameters.__subclasses__():
                if op_type == subcls.op_name:
                    return super(BinaryOpParameters, cls).__new__(subcls)
            raise ValueError(f'binary op {op_type} not found')

    def __init__(self, *args, op_type="maximum", **kwargs):
        super(BinaryOpParameters, self).__init__(*args, **kwargs)
        self._op_type = op_type

    @property
    def op_type(self):
        return self._op_type

    def get_output_size(self, in_dims):
        assert len(in_dims) == 2
        out_dim = in_dims[0].clone()
        return [out_dim]

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise ValueError('cannot clone')

    def __str__(self):
        return "{} {}".format(
            self._op_type,
            self.at_options
        )


@expression_op(Max)
class MaxOpParameters(BinaryOpParameters, InsensitiveToQuantization):
    op_name = 'maximum'


@expression_op(Min)
class MinOpParameters(BinaryOpParameters, InsensitiveToQuantization):
    op_name = 'minimum'


@expression_op(Pow)
class PowOpParameters(BinaryOpParameters):
    op_name = 'pow'


class UnaryOpParameters(CanFuseToExpression, Parameters):
    op_name = "unary"

    def __new__(cls, *args, op_type="sqrt", **kwargs):
        if cls == UnaryOpParameters:
            for subcls in UnaryOpParameters.__subclasses__():
                if op_type == subcls.op_name:
                    return super(UnaryOpParameters, cls).__new__(subcls)
            raise ValueError(f'unary op {op_type} not found')
        return super(UnaryOpParameters, cls).__new__(cls)

    def __init__(self, *args, op_type=None, **kwargs):
        super(UnaryOpParameters, self).__init__(*args, **kwargs)
        self._op_type = op_type

    @property
    def op_type(self):
        return self._op_type

    def get_output_size(self, in_dims):
        assert len(in_dims) == 1
        out_dim = in_dims[0].clone()
        return [out_dim]

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "{} {}".format(
            self._op_type,
            self.at_options
        )


@expression_op(Sqrt)
class SqrtOpParameters(UnaryOpParameters):
    op_name = 'sqrt'


@expression_op(Exp)
class ExpOpParameters(UnaryOpParameters):
    op_name = 'exp'


@expression_op(Log)
class LogOpParameters(UnaryOpParameters):
    op_name = 'log'


@expression_op(Abs)
class AbsOpParameters(UnaryOpParameters, InsensitiveToQuantization):
    op_name = 'abs'


@expression_op(Neg)
class NegOpParameters(UnaryOpParameters, InsensitiveToQuantization):
    op_name = 'neg'


class GlobalPoolParameters(Transposable, SingleInputAndOutput):
    op_name = "global"

    def __init__(self, *args, pool_type="max", axis=None, keep_dims=None, **kwargs):
        super(GlobalPoolParameters, self).__init__(*args, **kwargs)
        self._pool_type = pool_type
        self._axis = axis
        self._keep_dims = keep_dims

    @property
    def axis(self):
        return self._axis

    @property
    def keep_dims(self):
        return self._keep_dims

    @property
    def pool_type(self):
        return self._pool_type

    @axis.setter
    def axis(self, val):
        self._axis = val

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        out_dim = in_dims[0].clone()
        if self.transpose_in:
            out_dim.transpose(self.transpose_in[0])

        if self.keep_dims:
            names = out_dim.keys if out_dim.is_named else None
            out_dim = Dim(shape=[1 if idx in self._axis else dim
                                 for idx, dim in enumerate(out_dim.shape)],
                          names=names, is_ordered=True)
            if self.transpose_out:
                out_dim.transpose(self.transpose_out[0])
        else:
            out_dim = Dim(shape=[dim for idx, dim in enumerate(out_dim.shape)
                                 if idx not in self._axis],
                          is_ordered=True)

        return [out_dim]

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "{} A {}{} {} {}".format(
            self._pool_type,
            self._axis,
            " keep_dims " if self._keep_dims else "",
            Transposable.__str__(self),
            self.at_options
        )


class ReshapeParameters(Transposable, SingleInputAndOutput, InsensitiveToQuantization):
    '''This class covers reshapes and transposes'''

    op_name = "reshape"

    def __init__(self, *args, old_shape=None, shape=None, **kwargs):
        super(ReshapeParameters, self).__init__(
            *args, eliminate_transposes_pass_down=True, eliminate_transposes_pass_up=True, **kwargs)
        if not isinstance(shape, Dim):
            shape = Dim.unnamed(shape)
        self._shape = shape
        self._old_shape = old_shape

    def does_nothing(self):
        return self.shape.layout_shape == self.old_shape.layout_shape

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        assert len(in_dims) == 1
        self.in_dims = self.clone_dim_with_hints(in_dims)
        in_dim = in_dims[0]
        self._old_shape = in_dim
        if in_dim.size() != self.shape.size():
            raise NotImplementedError("bad reshape %s: in dim %s does not match reshape %s" %
                                      (self.name, in_dim, self.shape))
        out = self.shape.clone()
        if self.transpose_out:
            out.transpose(self.transpose_out[0])
        return [out]

    @property
    def shape(self):
        return self._shape

    @shape.setter
    def shape(self, val):
        self._shape = val

    @property
    def old_shape(self):
        return self._old_shape

    @old_shape.setter
    def old_shape(self, val):
        self._old_shape = val

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "SHAPE {} {}".format(
            self.shape,
            Transposable.__str__(self)
        )


# pylint: disable=abstract-method


class NoOPParameters(NoSizeChangeParameters, SingleInputAndOutput, InsensitiveToQuantization):
    op_name = "noop"

    def __init__(self, name, desc=""):
        super(NoOPParameters, self).__init__(name)
        self._desc = desc

    def get_parameter_size(self):
        return 0

    @property
    def can_equalize(self):
        return False

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def compute_load(self):
        return 0

    def __str__(self):
        return "NOOP {}".format(
            self._desc
        )


class UnexecutableOpParameters(Parameters):
    pass


class UnconvertedOpParameters(UnexecutableOpParameters):

    def __init__(self, name, indicated_op_name=None, expected_inputs=None,
                 indicated_outputs=None, info=None, **kwargs):
        super(UnconvertedOpParameters, self).__init__(name, **kwargs)
        self.info = info
        self.expected_inputs = expected_inputs
        self.indicated_outputs = indicated_outputs
        self.indicated_op_name = indicated_op_name

    @property
    def op_name(self):
        return "UNSUPPORTED"

    def get_output_size(self, in_dims):
        if self.indicated_outputs:
            return self.indicated_outputs
        self.in_dims = self.clone_dim_with_hints(in_dims)
        if len(self.in_dims) == 1:
            return [self.in_dims[0]]
        return [Dim.unknown()]

    @property
    def can_equalize(self):
        return False

    def get_parameter_size(self):
        return 0

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "UNSUPPORTED OP: %s" % self.indicated_op_name


class UnknownOpParameters(UnexecutableOpParameters):

    def __init__(self, name, info):
        super(UnknownOpParameters, self).__init__(name)
        self.info = info

    def get_output_size(self, in_dims):
        self.in_dims = self.clone_dim_with_hints(in_dims)
        if len(self.in_dims) == 1:
            return [self.in_dims[0]]
        return [Dim.unknown()]

    @property
    def can_equalize(self):
        return False

    def get_parameter_size(self):
        return 0

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def __str__(self):
        return "Unknown"
