
/* THIS FILE HAS BEEN GENERATED, DO NOT MODIFY IT.
 */

/*
 * Copyright (C) 2020 GreenWaves Technologies
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef __ARCHI_CLUSTER_CTRL_UNIT_ACCESSORS__
#define __ARCHI_CLUSTER_CTRL_UNIT_ACCESSORS__

#if !defined(LANGUAGE_ASSEMBLY) && !defined(__ASSEMBLER__)

#include <stdint.h>
#include "archi/gap_utils.h"

#endif




//
// REGISTERS ACCESS FUNCTIONS
//

#if !defined(LANGUAGE_ASSEMBLY) && !defined(__ASSEMBLER__)

static inline uint32_t cluster_ctrl_unit_fetch_en_get(uint32_t base)
{
    return GAP_READ(base, CLUSTER_CTRL_UNIT_FETCH_EN_OFFSET);
}

static inline void cluster_ctrl_unit_fetch_en_set(uint32_t base, uint32_t value)
{
    GAP_WRITE(base, CLUSTER_CTRL_UNIT_FETCH_EN_OFFSET, value);
}


static inline uint32_t cluster_ctrl_unit_clock_gate_get(uint32_t base)
{
    return GAP_READ(base, CLUSTER_CTRL_UNIT_CLOCK_GATE_OFFSET);
}

static inline void cluster_ctrl_unit_clock_gate_set(uint32_t base, uint32_t value)
{
    GAP_WRITE(base, CLUSTER_CTRL_UNIT_CLOCK_GATE_OFFSET, value);
}


static inline uint32_t cluster_ctrl_unit_boot_addr0_get(uint32_t base)
{
    return GAP_READ(base, CLUSTER_CTRL_UNIT_BOOT_ADDR0_OFFSET);
}

static inline void cluster_ctrl_unit_boot_addr0_set(uint32_t base, uint32_t value)
{
    GAP_WRITE(base, CLUSTER_CTRL_UNIT_BOOT_ADDR0_OFFSET, value);
}


#endif

#endif