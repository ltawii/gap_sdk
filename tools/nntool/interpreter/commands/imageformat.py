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

import argparse
from copy import deepcopy

from cmd2 import Cmd2ArgumentParser, with_argparser

from graph.types import ImageFormatParameters, NNEdge, TransposeParameters
from interpreter.nntool_shell_base import NNToolShellBase
from quantization.multiplicative.mult_quantization import \
    MultQuantizationRecordBase
from quantization.qtype import QType
from quantization.symmetric.symmetric_quantization import \
    SymmetricQuantizationBase
from utils.node_id import NodeId


class ImageFormatCommand(NNToolShellBase):
    def inputs_choices(self):
        if self.G is None:
            return []
        return [node.name for node in self.G.inputs()]

    def format_choices(self):
        return [fmt.lower() for fmt in ImageFormatParameters.FORMAT_CHANGES] + ['none']

    def norm_choices(self):
        return [fmt.lower() for fmt in ImageFormatParameters.NORMALIZATIONS] + ['none']

    # IMAGEFORMAT COMMAND
    parser_imageformat = Cmd2ArgumentParser("inserts image format node into graphs")
    parser_imageformat.add_argument('input_node',
                                    choices_method=inputs_choices,
                                    help='input node name to format')
    parser_imageformat.add_argument('image_formatter',
                                    choices_method=format_choices,
                                    help='input node name to format')
    parser_imageformat.add_argument('image_normalizer',
                                    choices_method=norm_choices,
                                    help='input node name to format')

    @with_argparser(parser_imageformat)
    def do_imageformat(self, args: argparse.Namespace):
        """ Add or modify image format options."""
        self._check_graph()
        if args.input_node not in self.G:
            self.perror("input node not found")
            return
        input_node = self.G[args.input_node]
        out_edges = self.G.out_edges(input_node.name)
        if len(out_edges) == 1 and isinstance(out_edges[0].to_node, ImageFormatParameters):
            self.G.changes.image_format(input_node.name, None, None)
            remove_formatter(self.G, out_edges[0].to_node)
            self.G.add_dimensions()
            return
        if args.image_formatter == "none" and args.image_normalizer == "none":
            self.pfeedback("no formatting set")
            self.G.add_dimensions()
            return
        self.G.changes.image_format(input_node.name, args.image_formatter, args.image_normalizer)
        insert_formatter(self.G, input_node, args.image_formatter, args.image_normalizer)
        self.G.add_dimensions()


def insert_formatter(G, input_node, formatter, normalizer):
    format_node = ImageFormatParameters(input_node.name + "_formatter",
                                        norm_func=normalizer.upper(),
                                        format_change=formatter.upper())
    out_edges = G.out_edges(input_node.name)

    # dims updated to reflect formatter
    if format_node.output_channels is not None and format_node.input_channels is not None:
        out_dim = input_node.get_output_size(None)[0]
        if formatter.upper() in ("BW8", "BW16"):
            assert format_node.input_channels == 1
            in_dim = out_dim.clone()
            format_node.out_dims_hint = input_node.out_dims_hint
            format_node.in_dims_hint = input_node.out_dims_hint
            input_node.dims = in_dim
            for out_edge in out_edges:
                G.remove_edge(out_edge)
        else:
            if not out_dim.is_named or out_dim.c != format_node.output_channels:
                raise ValueError(
                    "current graph input is not named or does not match formatter output channels")
            if formatter.upper() in ("RGB16", "BW16") and normalizer.upper() != "OUT_INT16":
                raise ValueError(
                    "rgb16 and bw16 formatters must have out_int16 as normalization function")
            in_dim = out_dim.clone()
            in_dim.c = format_node.input_channels
            in_dim.impose_order(("h", "w", "c"))
            format_node.in_dims_hint = [["h", "w", "c"]]
            input_node.dims = in_dim
            if input_node.fixed_order:
                new_out_edges = []
                for out_edge in out_edges:
                    if isinstance(out_edge.to_node, TransposeParameters):
                        trans_node = out_edge.to_node
                        transpose_edges = G.out_edges(trans_node.name)
                        new_out_edges.extend(transpose_edges)
                        G.remove(trans_node)
                        if G.quantization:
                            nid = NodeId(trans_node)
                            if nid in G.quantization:
                                del G.quantization[NodeId(trans_node)]
                    else:
                        new_out_edges.append(out_edge)
                out_edges = new_out_edges
            else:
                input_node.fixed_order = True
                for out_edge in out_edges:
                    G.remove_edge(out_edge)
            format_node.out_dims_hint = [["c", "h", "w"]] * len(out_edges)
            input_node.out_dims_hint = [["h", "w", "c"]]
            G.node_options[NodeId(input_node)] = input_node.at_options
    # qrec updated to reflect formatter
    input_qrec = G.quantization and G.quantization.get(NodeId(input_node))
    if input_qrec and format_node.input_dtype and format_node.output_dtype:
        formatter_qrec = G.quantization.get(NodeId(format_node))
        if not formatter_qrec:
            if input_qrec.out_qs[0].dtype != format_node.output_dtype:
                raise ValueError(
                    "current graph input output quantization does not match formatter output")
            formatter_qrec = deepcopy(input_qrec)
            formatter_qrec.out_qs[0] = deepcopy(formatter_qrec.out_qs[0])
            if isinstance(formatter_qrec, MultQuantizationRecordBase):
                formatter_in_q = QType(scale=1, zero_point=0, dtype=format_node.input_dtype)
            elif isinstance(formatter_qrec, SymmetricQuantizationBase):
                formatter_in_q = QType(q=0, dtype=format_node.input_dtype)
            else:
                raise NotImplementedError("quantization has unknown type")
            if len(formatter_qrec.in_qs) > 0:
                formatter_qrec.in_qs[0] = formatter_in_q
                input_qrec.in_qs[0] = formatter_in_q
            else:
                formatter_qrec.in_qs.append(formatter_in_q)
                input_qrec.in_qs.append(formatter_in_q)
            input_qrec.out_qs[0] = formatter_in_q
        G.quantization[NodeId(format_node)] = formatter_qrec

    G.add_node(format_node)
    G.add_edge(NNEdge(input_node, format_node))
    for out_edge in out_edges:
        G.add_edge(NNEdge(format_node, out_edge.to_node, to_idx=out_edge.to_idx))


def remove_formatter(G, fmt_node):
    input_edges = G.in_edges(fmt_node.name)
    assert len(input_edges) == 1, "formatter node should only have one input"
    input_node = input_edges[0].from_node
    fmt_edges = G.out_edges(fmt_node.name)
    fmt_qrec = G.quantization and G.quantization.get(NodeId(fmt_node))
    G.remove(fmt_node)

    input_node.dims = fmt_node.out_dims[0]
    input_node.out_dims_hint = fmt_node.out_dims_hint
    for fmt_edge in fmt_edges:
        G.add_edge(NNEdge(input_node, fmt_edge.to_node, to_idx=fmt_edge.to_idx))
    if fmt_qrec:
        input_qrec = G.quantization[NodeId(input_node)]
        input_qrec.out_qs = fmt_qrec.out_qs
        input_qrec.in_qs = fmt_qrec.out_qs
        G.quantization.remove_node(fmt_node)
