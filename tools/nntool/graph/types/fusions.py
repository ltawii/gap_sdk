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
from ..dim import Dim
from .base import (Parameters, NodeOptions, FilterParameters,
                   SensitiveToOrder, SingleInputAndOutput, NNEdge)

LOG = logging.getLogger("nntool." + __name__)


def insert_ext(l, elem, idx):
    if idx >= len(l):
        l.extend([None]*(idx + 1 - len(l)))
    l[idx] = elem


class FusionInputOutputParameters(Parameters):

    def __init__(self, *args, idx=0, dims=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.dims = dims
        self.idx = idx

    @property
    def can_equalize(self):
        return False

    def get_output_size(self, in_dims):
        self.dims = in_dims[0].clone()
        return [self.dims]

    def get_parameter_size(self):
        return 0

    def clone(self, name, groupn=None):
        return self.__class__(name)

    def __str__(self):
        return ""


class FusionInputParameters(FusionInputOutputParameters):
    op_name = "fusion_input"


class FusionOutputParameters(FusionInputOutputParameters):
    op_name = "fusion_output"


class FusionBase(Parameters):
    fusion_op_name = "!!NOT SET!!"

    def __init__(self, name, *args, fusion_type=None, subgraph=None,
                 input_mapping=None,
                 output_mapping=None,
                 in_dims=None, out_dims=None,
                 inout_set=False, **kwargs):
        # output_mapping [(int_node1, 1), (int_node2, 0), ....]
        # input mapping list of list inputs [[(int_node1, 1), (int_node2, 0)], ....]
        super(FusionBase, self).__init__(name, *args, **kwargs)
        # subgraph = deepcopy(subgraph)
        self._subgraph = subgraph
        if not inout_set:
            in_hints = kwargs.get('in_dims_hint')
            out_hints = kwargs.get('out_dims_hint')
            nodes = self.contained_nodes()
            if input_mapping is None:
                input_mapping = [[(nodes[0], 0)]]

            for from_idx, node_list in enumerate(input_mapping):
                hint = [in_hints[from_idx]] if in_hints and len(in_hints) > from_idx else None
                dims = in_dims[from_idx] if in_dims and len(in_dims) > from_idx else None
                input_node = FusionInputParameters("%s_in_%s" % (name, from_idx),
                                                   idx=from_idx,
                                                   dims=dims,
                                                   in_dims_hint=hint, out_dims_hint=hint)
                for node, to_idx in node_list:
                    subgraph.add_edge(NNEdge(input_node, node, to_idx=to_idx))

            if output_mapping is None:
                output_mapping = [(nodes[-1], 0)]

            for to_idx, (node, from_idx) in enumerate(output_mapping):
                hint = [out_hints[to_idx]] if out_hints and len(out_hints) > to_idx else None
                output_node = FusionOutputParameters("%s_out_%s" % (name, to_idx),
                                                     idx=to_idx,
                                                     in_dims_hint=hint, out_dims_hint=hint)
                subgraph.add_edge(NNEdge(node, output_node, from_idx=from_idx))

        inputs_by_idx = sorted(list({node.idx: node for node in subgraph.nodes()
                                     if isinstance(node, FusionInputParameters)}.values()),
                               key=lambda x: x.idx)
        outputs_by_idx = sorted([node for node in subgraph.nodes()
                                 if isinstance(node, FusionOutputParameters)],
                                key=lambda x: x.idx)

        if not self.in_dims_hint:
            self.in_dims_hint = [None]*len(inputs_by_idx)
            for idx, node in enumerate(inputs_by_idx):
                edge = subgraph.out_edges(node.name)[0]
                if edge.to_node.in_dims_hint:
                    self.in_dims_hint[idx] = edge.to_node.in_dims_hint[edge.to_idx]
            if all(hint is None for hint in self.in_dims_hint):
                self.in_dims_hint = None
        if in_dims is not None:
            self.in_dims = in_dims
        if not self.out_dims_hint:
            self.out_dims_hint = [None]*len(outputs_by_idx)
            for idx, node in enumerate(outputs_by_idx):
                edge = subgraph.in_edges(node.name)[0]
                if edge.to_node.out_dims_hint:
                    self.out_dims_hint[idx] = edge.from_node.out_dims_hint[edge.from_idx]
            if all(hint is None for hint in self.out_dims_hint):
                self.out_dims_hint = None
        if out_dims is not None:
            self.out_dims = out_dims

        self.fusion_type = fusion_type

    @staticmethod
    def get_mapping_from_edges(edges):
        mappings = {}
        for from_idx, edge in enumerate(edges):
            node_mappings = mappings.get(edge.to_node)
            if not node_mappings:
                node_mappings = {}
                mappings[edge.to_node] = node_mappings
            node_mappings[from_idx] = edge.to_idx
        return mappings

    @property
    def op_name(self):
        if self.fusion_type:
            return self.fusion_op_name + '_' + self.fusion_type
        return self.fusion_op_name

    @property
    def subgraph(self):
        return self._subgraph

    def contained_nodes(self):
        return [node for node in self.subgraph.dfs()
                if not isinstance(node, FusionInputOutputParameters)]

    def get_contained_node(self, name):
        return next((n for n in self.contained_nodes() if n.name == name), None)

    @property
    def can_equalize(self):
        return all([param.can_equalize for param in self.contained_nodes()])

    @staticmethod
    def convert_input_mapping(input_mapping):
        orig = []
        for node, edges in input_mapping.items():
            for from_idx, to_idx in edges.items():
                if from_idx >= len(orig) or not isinstance(orig[from_idx], list):
                    inps = []
                    insert_ext(orig, inps, from_idx)
                else:
                    inps = orig[from_idx]
                inps.append((node, to_idx))
        return orig

    @staticmethod
    def convert_output_mapping(output_mapping):
        orig = []
        for node, edges in output_mapping.items():
            for from_idx, to_idx in edges.items():
                insert_ext(orig, (node, from_idx), to_idx)
        return orig

    def clone(self, name, groupn=None):
        raise NotImplementedError()

    def get_parameter_size(self):
        return 0

    def get_output_size(self, in_dims):
        self.in_dims = self.clone_dim_with_hints(in_dims)
        node_out_dims = []
        for node in self.subgraph.dfs():
            if isinstance(node, FusionInputParameters):
                node_in_dims = [self.clone_dim_with_hint(in_dims[node.idx], node.idx)]
            else:
                node_in_dims = []
                for edge in self.subgraph.in_edges(node.name):
                    insert_ext(node_in_dims, edge.from_node.out_dims[edge.from_idx], edge.to_idx)
            node.in_dims = [dim.clone() if dim else None for dim in node_in_dims]
            out_dims = node.get_output_size(node.in_dims)
            node.out_dims = out_dims
            if isinstance(node, FusionOutputParameters):
                insert_ext(node_out_dims, out_dims[0], node.idx)
        self.out_dims = node_out_dims
        return node_out_dims

    def __str__(self):
        return "{}".format(", ".join([str(node).strip() for node in self.contained_nodes()]))


class MatScaleFusionParameters(FusionBase, SensitiveToOrder):
    fusion_op_name = "matscale"

    def __init__(self, *args, activation=None, **kwargs):
        self.activation = activation
        super(MatScaleFusionParameters, self).__init__(*args, **kwargs)

    def get_output_size(self, in_dims):
        return [Dim.broadcast(in_dims)]


class ConvFusionParameters(FusionBase, SingleInputAndOutput, SensitiveToOrder):
    '''Fusion of operators. At present restricted to single input and output but
    this could be removed perhaps'''

    fusion_op_name = "conv_fusion"

    def _init_at_options(self):
        if self._at_options is None:
            self._at_options = NodeOptions(None)
        self._at_options.extend(*[node.at_options for node in self.contained_nodes()])

    @property
    def at_options(self):
        self._init_at_options()
        return self._at_options

    @at_options.setter
    def gen_ctrl(self, val):
        self._init_at_options()
        self._at_options = val

    def contained_filters(self):
        return [x for x in self.contained_nodes() if isinstance(x, FilterParameters)]

    def get_parameter_size(self):
        return sum([node.get_parameter_size() for node in self.contained_nodes()])

    def __str__(self):
        return "{} {}".format(", ".join([str(node).strip() for node in self.contained_nodes()]), self.gen_ctrl or "")

    def compute_load(self):
        return sum([load if load else 0 for load in [node.compute_load()
                                                     for node in self.contained_nodes()]])

class PaddedAddFusionParameters(FusionBase, SensitiveToOrder):
    fusion_op_name = "padded_add_fusion"

    def _init_at_options(self):
        if self._at_options is None:
            self._at_options = NodeOptions(None)
        self._at_options.extend(*[node.at_options for node in self.contained_nodes()])

    @property
    def at_options(self):
        self._init_at_options()
        return self._at_options

    @at_options.setter
    def gen_ctrl(self, val):
        self._init_at_options()
        self._at_options = val

    def get_parameter_size(self):
        return 0

    def __str__(self):
        return "{} {}".format(", ".join([str(node).strip() for node in self.contained_nodes()]), self.gen_ctrl or "")

    def compute_load(self):
        return sum([load if load else 0 for load in [node.compute_load()
                                                     for node in self.contained_nodes()]])

class MatMulOpFusionParameters(FusionBase, SingleInputAndOutput, SensitiveToOrder):
    '''Fusion of operators. At present restricted to single input and output but
    this could be removed perhaps'''

    fusion_op_name = "fusion"

    def _init_at_options(self):
        if self._at_options is None:
            self._at_options = NodeOptions(None)
        self._at_options.extend(*[node.at_options for node in self.contained_nodes()])

    @property
    def at_options(self):
        self._init_at_options()
        return self._at_options

    @at_options.setter
    def gen_ctrl(self, val):
        self._init_at_options()
        self._at_options = val

    def get_parameter_size(self):
        return sum([node.get_parameter_size() for node in self.contained_nodes()])

    def __str__(self):
        return "{} {}".format(", ".join([str(node).strip() for node in self.contained_nodes()]), self.gen_ctrl or "")

    def compute_load(self):
        return sum([load if load else 0 for load in [node.compute_load()
                                                     for node in self.contained_nodes()]])

class ActivationFusion(FusionBase):
    fusion_op_name = "activation_fusion"


class PieceWiseFusion(FusionBase):
    fusion_op_name = "activation_fusion"
