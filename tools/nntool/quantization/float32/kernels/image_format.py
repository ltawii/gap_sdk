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

import numpy as np
from graph.types import ImageFormatParameters
from quantization.float32.float32_quantization import Float32QuantizationRecord
from quantization.float32.float16_quantization import Float16QuantizationRecord
from quantization.float32.bfloat16_quantization import Bfloat16QuantizationRecord
from quantization.kernels.kernel_base import (KernelBase, params_type,
                                              quantization)
from quantization.quantization_record_base import QuantizationRecordBase
from utils.formatters import FORMAT_CHANGES, NORMALIZATIONS


@params_type(ImageFormatParameters)
@quantization('float32')
class ImageFormatFloat32(KernelBase):
    @classmethod
    def execute(cls, params,
                in_tensors,
                qrec: QuantizationRecordBase,
                **kwargs):

        in_dim = params.in_dims[0]
        out_dim = params.out_dims[0]
        res = in_tensors[0]
        res = FORMAT_CHANGES[params.format_change](res, in_dim, out_dim)
        res = NORMALIZATIONS[params.norm_func](res)
        if qrec is None or isinstance(qrec, (Float32QuantizationRecord,
                                             Float16QuantizationRecord,
                                             Bfloat16QuantizationRecord)):
            iinfo = np.iinfo(res.dtype)
            if res.dtype == np.int8 or res.dtype == np.int16:
                res = res.astype(qrec.dtype(ktype="float32")) / -iinfo.min
            else:
                raise ValueError("unsure how to dequantize this output from imageformatter")
            return [res]
        return [qrec.out_qs[0].dequantize(res) if qrec.out_qs else res]
