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

#include "pmsis.h"
#include "pmsis/rtos/os_frontend_api/pmsis_time.h"
#include "bsp/bsp.h"
#include "bsp/camera/hm0360.h"
#include "hm0360.h"

typedef struct {
    uint16_t addr;
    uint8_t value;
} i2c_req_t;


typedef struct {
    struct pi_device cpi_device;
    struct pi_device i2c_device;
    i2c_req_t i2c_req;
    uint32_t i2c_read_value;
    int is_awake;
} hm0360_t;

typedef struct {
    uint16_t addr;
    uint8_t data;
} hm0360_reg_init_t;

static hm0360_reg_init_t __hm0360_reg_init[] = {
    //{HM0360_PMU_CFG_3, 0x0}, // disable context switch
    //{HM0360_IMAGE_ORIENTATION, 0x0},
    //{HM0360_WIN_MODE, 0x1}, // 640x480
    //{HM0360_OUTPUT_EN, 0x1}, // enable output
    //{HM0360_FRAME_OUTPUT_EN, 0x1}, // parallel output
    //{HM0360_TEST_PATTERN_MODE, 0x1}, // enable test pattern
    //{HM0360_STROBE_CFG, 0x1}, // enable strobe
    //{HM0360_PMU_CFG_7, 0x1}, // frame output number
    //{HM0360_COMMAND_UPDATE, 0x1}, // command update
    {0x0103, 0x00},
    {0x0350, 0xE0},
    {0x0370, 0x00},
    {0x0371, 0x00},
    {0x0372, 0x01},
    {0x1000, 0x43},
    {0x1001, 0x80},
    {0x1003, 0x20},
    {0x1004, 0x20},
    {0x1007, 0x01},
    {0x1008, 0x20},
    {0x1009, 0x20},
    {0x100A, 0x05},
    {0x100B, 0x20},
    {0x100C, 0x20},
    {0x1013, 0x00},
    {0x1014, 0x01},
    {0x1018, 0x00},
    {0x101D, 0xCF},
    {0x101E, 0x01},
    {0x101F, 0x00},
    {0x1020, 0x01},
    {0x1021, 0x5D},
    {0x102F, 0x08},
    {0x1030, 0x04},
    {0x1031, 0x08},
    {0x1032, 0x10},
    {0x1033, 0x18},
    {0x1034, 0x20},
    {0x1035, 0x28},
    {0x1036, 0x30},
    {0x1037, 0x38},
    {0x1038, 0x40},
    {0x1039, 0x50},
    {0x103A, 0x60},
    {0x103B, 0x70},
    {0x103C, 0x80},
    {0x103D, 0xA0},
    {0x103E, 0xC0},
    {0x103F, 0xE0},
    {0x1041, 0x00},
    {0x2000, 0x7F},
    {0x202B, 0x03},
    {0x202C, 0x03},
    {0x202D, 0x00},
    {0x2031, 0x60},
    {0x2032, 0x08},
    {0x2036, 0x19},
    {0x2037, 0x08},
    {0x2038, 0x10},
    {0x203C, 0x01},
    {0x203D, 0x04},
    {0x203E, 0x01},
    {0x203F, 0x38},
    {0x2048, 0x00},
    {0x2049, 0x10},
    {0x204A, 0x40},
    {0x204B, 0x00},
    {0x204C, 0x08},
    {0x204D, 0x20},
    {0x204E, 0x00},
    {0x204F, 0x38},
    {0x2050, 0xE0},
    {0x2051, 0x00},
    {0x2052, 0x1C},
    {0x2053, 0x70},
    {0x2054, 0x00},
    {0x2055, 0x1A},
    {0x2056, 0xC0},
    {0x2057, 0x00},
    {0x2058, 0x06},
    {0x2059, 0xB0},
    {0x2061, 0x00},
    {0x2062, 0x00},
    {0x2063, 0xC8},
    {0x2080, 0x41},
    {0x2081, 0xE0},
    {0x2082, 0xF0},
    {0x2083, 0x01},
    {0x2084, 0x10},
    {0x2085, 0x10},
    {0x2086, 0x01},
    {0x2087, 0x06},
    {0x2088, 0x0C},
    {0x2089, 0x12},
    {0x208A, 0x1C},
    {0x208B, 0x30},
    {0x208C, 0x10},
    {0x208D, 0x02},
    {0x208E, 0x08},
    {0x208F, 0x0D},
    {0x2090, 0x14},
    {0x2091, 0x1D},
    {0x2092, 0x30},
    {0x2093, 0x08},
    {0x2094, 0x0A},
    {0x2095, 0x0F},
    {0x2096, 0x14},
    {0x2097, 0x18},
    {0x2098, 0x20},
    {0x2099, 0x10},
    {0x209A, 0x00},
    {0x209B, 0x01},
    {0x209C, 0x01},
    {0x209D, 0x11},
    {0x209E, 0x06},
    {0x209F, 0x20},
    {0x20A0, 0x10},
    {0x2590, 0x01},
    {0x2800, 0x00},
    {0x2804, 0x02},
    {0x2805, 0x03},
    {0x2806, 0x03},
    {0x2807, 0x08},
    {0x2808, 0x04},
    {0x2809, 0x0C},
    {0x280A, 0x03},
    {0x280F, 0x03},
    {0x2810, 0x03},
    {0x2811, 0x00},
    {0x2812, 0x09},
    {0x2821, 0xDE},
    {0x3010, 0x00},
    {0x3013, 0x01},
    {0x3019, 0x00},
    {0x301A, 0x00},
    {0x301B, 0x20},
    {0x301C, 0xFF},
    {0x3020, 0x00},
    {0x3021, 0x00},
    {0x3024, 0x00},
    {0x3025, 0x12},
    {0x3026, 0x03},
    {0x3027, 0x81},
    {0x3028, 0x01},
    {0x3029, 0x00},
    {0x302A, 0x30},
    {0x302B, 0x2A},
    {0x302C, 0x00},
    {0x302D, 0x03},
    {0x302E, 0x00},
    {0x302F, 0x00},
    {0x3031, 0x01},
    {0x3034, 0x00},
    {0x3035, 0x01},
    {0x3051, 0x00},
    {0x305C, 0x03},
    {0x3060, 0x00},
    {0x3061, 0xFA},
    {0x3062, 0xFF},
    {0x3063, 0xFF},
    {0x3064, 0xFF},
    {0x3065, 0xFF},
    {0x3066, 0xFF},
    {0x3067, 0xFF},
    {0x3068, 0xFF},
    {0x3069, 0xFF},
    {0x306A, 0xFF},
    {0x306B, 0xFF},
    {0x306C, 0xFF},
    {0x306D, 0xFF},
    {0x306E, 0xFF},
    {0x306F, 0xFF},
    {0x3070, 0xFF},
    {0x3071, 0xFF},
    {0x3072, 0xFF},
    {0x3073, 0xFF},
    {0x3074, 0xFF},
    {0x3075, 0xFF},
    {0x3076, 0xFF},
    {0x3077, 0xFF},
    {0x3078, 0xFF},
    {0x3079, 0xFF},
    {0x307A, 0xFF},
    {0x307B, 0xFF},
    {0x307C, 0xFF},
    {0x307D, 0xFF},
    {0x307E, 0xFF},
    {0x307F, 0xFF},
    {0x3080, 0x00},
    {0x3081, 0x00},
    {0x3082, 0x00},
    {0x3083, 0x20},
    {0x3084, 0x00},
    {0x3085, 0x20},
    {0x3086, 0x00},
    {0x3087, 0x20},
    {0x3088, 0x00},
    {0x3089, 0x04},
    {0x3094, 0x02},
    {0x3095, 0x02},
    {0x3096, 0x00},
    {0x3097, 0x02},
    {0x3098, 0x00},
    {0x3099, 0x02},
    {0x309E, 0x05},
    {0x309F, 0x02},
    {0x30A0, 0x02},
    {0x30A1, 0x00},
    {0x30A2, 0x08},
    {0x30A3, 0x00},
    {0x30A4, 0x20},
    {0x30A5, 0x04},
    {0x30A6, 0x02},
    {0x30A7, 0x02},
    {0x30A8, 0x01},
    {0x30A9, 0x00},
    {0x30AA, 0x02},
    {0x30AB, 0x34},
    {0x30B0, 0x03},
    {0x30C4, 0x10},
    {0x30C5, 0x01},
    {0x30C6, 0xBF},
    {0x30C7, 0x00},
    {0x30C8, 0x00},
    {0x30CB, 0xFF},
    {0x30CC, 0xFF},
    {0x30CD, 0x7F},
    {0x30CE, 0x7F},
    {0x30D3, 0x01},
    {0x30D4, 0xFF},
    {0x30D5, 0x00},
    {0x30D6, 0xFF},
    {0x30D7, 0x00},
    {0x30D8, 0xA7},
    {0x30D9, 0x05},
    {0x30DA, 0x40},
    {0x30DB, 0xFF},
    {0x30DC, 0x00},
    {0x30DD, 0x27},
    {0x30DE, 0x05},
    {0x30DF, 0x80},
    {0x30E0, 0xFF},
    {0x30E1, 0x00},
    {0x30E2, 0x27},
    {0x30E3, 0x05},
    {0x30E4, 0xC0},
    {0x30E5, 0xFF},
    {0x30E6, 0x00},
    {0x30E7, 0x27},
    {0x30E8, 0x05},
    {0x30E9, 0xC0},
    {0x30EA, 0xFF},
    {0x30EB, 0x00},
    {0x30EC, 0x27},
    {0x30ED, 0x05},
    {0x30EE, 0x00},
    {0x30EF, 0xFF},
    {0x30F0, 0x00},
    {0x30F1, 0xA7},
    {0x30F2, 0x05},
    {0x30F3, 0x40},
    {0x30F4, 0xFF},
    {0x30F5, 0x00},
    {0x30F6, 0x27},
    {0x30F7, 0x05},
    {0x30F8, 0x80},
    {0x30F9, 0xFF},
    {0x30FA, 0x00},
    {0x30FB, 0x27},
    {0x30FC, 0x05},
    {0x30FD, 0xC0},
    {0x30FE, 0xFF},
    {0x30FF, 0x00},
    {0x3100, 0x27},
    {0x3101, 0x05},
    {0x3102, 0xC0},
    {0x3103, 0xFF},
    {0x3104, 0x00},
    {0x3105, 0x27},
    {0x3106, 0x05},
    {0x310B, 0x10},
    {0x3112, 0x04},
    {0x3113, 0xA0},
    {0x3114, 0x67},
    {0x3115, 0x42},
    {0x3116, 0x10},
    {0x3117, 0x0A},
    {0x3118, 0x3F},
#if 0
    {0x311A, 0x31}, // FIXME capture seems to work without this
                    // No this reg in the datasheet
#endif
    {0x311C, 0x17},
    {0x311D, 0x02},
    {0x311E, 0x0F},
    {0x311F, 0x0E},
    {0x3120, 0x0D},
    {0x3121, 0x0F},
    {0x3122, 0x00},
    {0x3123, 0x1D},
    {0x3126, 0x03},
    {0x3128, 0x57},
    {0x312B, 0x41},
    {0x312E, 0x00},
    {0x312F, 0x00},
    {0x3130, 0x0C},
    {0x3142, 0x9F},
    {0x3147, 0x18},
    {0x3149, 0x18},
    {0x314B, 0x01},
    {0x3150, 0x50},
    {0x3152, 0x00},
    {0x3156, 0x2C},
    {0x315A, 0x05},
    {0x315B, 0x2F},
    {0x315C, 0xE3},
    {0x315F, 0x02},
    {0x3160, 0x1F},
    {0x3163, 0x1F},
    {0x3164, 0x77},
    {0x3165, 0x7F},
    {0x317B, 0x94},
    {0x317C, 0x00},
    {0x317D, 0x02},
    {0x318C, 0x00},
    {0x3500, 0x74},
    {0x3501, 0x0A},
    {0x3502, 0x77},
    {0x3503, 0x02},
    {0x3504, 0x14},
    {0x3505, 0x03},
    {0x3506, 0x00},
    {0x3507, 0x00},
    {0x3508, 0x00},
    {0x3509, 0x00},
    {0x350A, 0xFF},
    {0x350B, 0x00},
    {0x350C, 0x00},
    {0x350D, 0x01},
    {0x350F, 0x00},
    {0x3510, 0x03},
    {0x3512, 0x7F},
    {0x3513, 0x00},
    {0x3514, 0x00},
    {0x3515, 0x01},
    {0x3516, 0x00},
    {0x3517, 0x02},
    {0x3518, 0x00},
    {0x3519, 0x7F},
    {0x351A, 0x00},
    {0x351B, 0x5F},
    {0x351C, 0x00},
    {0x351D, 0x02},
    {0x351E, 0x08},
    {0x351F, 0x03},
    {0x3520, 0x03},
    {0x3521, 0x00},
    {0x3523, 0x60},
    {0x3524, 0x08},
    {0x3525, 0x19},
    {0x3526, 0x08},
    {0x3527, 0x10},
    {0x352A, 0x01},
    {0x352B, 0x04},
    {0x352C, 0x01},
    {0x352D, 0x38},
    {0x3535, 0x02},
    {0x3536, 0x03},
    {0x3537, 0x03},
    {0x3538, 0x08},
    {0x3539, 0x04},
    {0x353A, 0x0C},
    {0x353B, 0x03},
    {0x3540, 0x03},
    {0x3541, 0x03},
    {0x3542, 0x00},
    {0x3543, 0x09},
    {0x3549, 0x04},
    {0x354A, 0x35},
    {0x354B, 0x21},
    {0x354C, 0x01},
    {0x354D, 0xE0},
    {0x354E, 0xF0},
    {0x354F, 0x10},
    {0x3550, 0x10},
    {0x3551, 0x10},
    {0x3552, 0x20},
    {0x3553, 0x10},
    {0x3554, 0x01},
    {0x3555, 0x06},
    {0x3556, 0x0C},
    {0x3557, 0x12},
    {0x3558, 0x1C},
    {0x3559, 0x30},
    {0x355A, 0x74},
    {0x355B, 0x0A},
    {0x355C, 0x77},
    {0x355D, 0x01},
    {0x355E, 0x1C},
    {0x355F, 0x03},
    {0x3560, 0x00},
    {0x3561, 0x01},
    {0x3562, 0x01},
    {0x3563, 0x00},
    {0x3564, 0xFF},
    {0x3565, 0x00},
    {0x3566, 0x00},
    {0x3567, 0x01},
    {0x3569, 0x00},
    {0x356A, 0x03},
    {0x356C, 0x7F},
    {0x356D, 0x00},
    {0x356E, 0x00},
    {0x356F, 0x01},
    {0x3570, 0x00},
    {0x3571, 0x02},
    {0x3572, 0x00},
    {0x3573, 0x3F},
    {0x3574, 0x00},
    {0x3575, 0x2F},
    {0x3576, 0x00},
    {0x3577, 0x01},
    {0x3578, 0x04},
    {0x3579, 0x03},
    {0x357A, 0x03},
    {0x357B, 0x00},
    {0x357D, 0x60},
    {0x357E, 0x08},
    {0x357F, 0x19},
    {0x3580, 0x08},
    {0x3581, 0x10},
    {0x3584, 0x01},
    {0x3585, 0x04},
    {0x3586, 0x01},
    {0x3587, 0x38},
    {0x3588, 0x02},
    {0x3589, 0x12},
    {0x358A, 0x04},
    {0x358B, 0x24},
    {0x358C, 0x06},
    {0x358D, 0x36},
    {0x358F, 0x02},
    {0x3590, 0x03},
    {0x3591, 0x03},
    {0x3592, 0x08},
    {0x3593, 0x04},
    {0x3594, 0x0C},
    {0x3595, 0x03},
    {0x359A, 0x03},
    {0x359B, 0x03},
    {0x359C, 0x00},
    {0x359D, 0x09},
    {0x35A3, 0x02},
    {0x35A4, 0x03},
    {0x35A5, 0x21},
    {0x35A6, 0x01},
    {0x35A7, 0xE0},
    {0x35A8, 0xF0},
    {0x35A9, 0x10},
    {0x35AA, 0x10},
    {0x35AB, 0x10},
    {0x35AC, 0x20},
    {0x35AD, 0x10},
    {0x35AE, 0x01},
    {0x35AF, 0x06},
    {0x35B0, 0x0C},
    {0x35B1, 0x12},
    {0x35B2, 0x1C},
    {0x35B3, 0x30},
    {0x35B4, 0x74},
    {0x35B5, 0x0A},
    {0x35B6, 0x77},
    {0x35B7, 0x00},
    {0x35B8, 0x94},
    {0x35B9, 0x03},
    {0x35BA, 0x00},
    {0x35BB, 0x03},
    {0x35BD, 0x00},
    {0x35BE, 0xFF},
    {0x35BF, 0x00},
    {0x35C0, 0x01},
    {0x35C1, 0x01},
    {0x35C3, 0x00},
    {0x35C4, 0x00},
    {0x35C6, 0x7F},
    {0x35C7, 0x00},
    {0x35C8, 0x00},
    {0x35C9, 0x01},
    {0x35CA, 0x00},
    {0x35CB, 0x02},
    {0x35CC, 0x00},
    {0x35CD, 0x0F},
    {0x35CE, 0x00},
    {0x35CF, 0x0B},
    {0x35D0, 0x00},
    {0x35D3, 0x03},
    {0x35D7, 0x60},
    {0x35D8, 0x04},
    {0x35D9, 0x20},
    {0x35DA, 0x08},
    {0x35DB, 0x14},
    {0x35DC, 0x60},
    {0x35DE, 0x00},
    {0x35DF, 0x82},
    {0x35E9, 0x02},
    {0x35EA, 0x03},
    {0x35EB, 0x03},
    {0x35EC, 0x08},
    {0x35ED, 0x04},
    {0x35EE, 0x0C},
    {0x35EF, 0x03},
    {0x35F4, 0x03},
    {0x35F5, 0x03},
    {0x35F6, 0x00},
    {0x35F7, 0x09},
    {0x35FD, 0x00},
    {0x35FE, 0x5E},
    {0x0104, 0x01},
    {0x0100, 0x01},
};

static inline int is_i2c_active()
{
#if defined(ARCHI_PLATFORM_RTL)

    // I2C driver is not yet working on some chips, at least this works on gvsoc.
    // Also there is noI2C connection to camera model on RTL
#if PULP_CHIP == CHIP_GAP9 || PULP_CHIP == CHIP_VEGA || PULP_CHIP == CHIP_ARNOLD || PULP_CHIP == CHIP_PULPISSIMO || PULP_CHIP == CHIP_PULPISSIMO_V1
    return 0;
#else
    return rt_platform() != ARCHI_PLATFORM_RTL;
#endif

#else

    return 1;

#endif
}



static void __hm0360_reg_write(hm0360_t *hm0360, uint16_t addr, uint8_t value)
{
    if (is_i2c_active())
    {
        hm0360->i2c_req.value = value;
        hm0360->i2c_req.addr = ((addr >> 8) & 0xff) | ((addr & 0xff) << 8);
        //printf("Addr: %x, req_addr: %x\n", addr, hm0360->i2c_req.addr);
        pi_i2c_write(&hm0360->i2c_device, (uint8_t *)&hm0360->i2c_req, 3, PI_I2C_XFER_STOP);
    }
}



static uint8_t __hm0360_reg_read(hm0360_t *hm0360, uint16_t addr)
{
    if (is_i2c_active())
    {
        hm0360->i2c_req.addr = ((addr >> 8) & 0xff) | ((addr & 0xff) << 8);
        pi_i2c_write(&hm0360->i2c_device, (uint8_t *)&hm0360->i2c_req, 2, PI_I2C_XFER_NO_STOP);
        pi_i2c_read(&hm0360->i2c_device, (uint8_t *)&hm0360->i2c_read_value, 1, PI_I2C_XFER_STOP);
        return *(volatile uint8_t *)&hm0360->i2c_read_value;
    }
    else
    {
        return 0;
    }
}



static void __hm0360_init_regs(hm0360_t *hm0360)
{
    int32_t i;
    for(i=0; i<(int32_t)(sizeof(__hm0360_reg_init)/sizeof(hm0360_reg_init_t)); i++)
    {
        __hm0360_reg_write(hm0360, __hm0360_reg_init[i].addr, __hm0360_reg_init[i].data);
    }
}



static void __hm0360_reset(hm0360_t *hm0360)
{
    __hm0360_reg_write(hm0360, HM0360_SW_RESET, HM0360_RESET);

    while (__hm0360_reg_read(hm0360, HM0360_MODE_SELECT) != HM0360_STANDBY)
    {
        __hm0360_reg_write(hm0360, HM0360_SW_RESET, HM0360_RESET);
        pi_time_wait_us(50);
    }
}



static void __hm0360_mode(hm0360_t *hm0360, uint8_t mode)
{
    __hm0360_reg_write(hm0360, HM0360_MODE_SELECT, mode);
}

static void __hm0360_wakeup(hm0360_t *hm0360)
{
    if (!hm0360->is_awake)
    {
        __hm0360_mode(hm0360, HM0360_STREAMING1);
        hm0360->is_awake = 1;
    }
}



static void __hm0360_standby(hm0360_t *hm0360)
{
    if (hm0360->is_awake)
    {
        __hm0360_mode(hm0360, HM0360_STANDBY);
        hm0360->is_awake = 0;
    }
}



int32_t __hm0360_open(struct pi_device *device)
{
    struct pi_hm0360_conf *conf = (struct pi_hm0360_conf *)device->config;

    hm0360_t *hm0360 = (hm0360_t *)pmsis_l2_malloc(sizeof(hm0360_t));
    if (hm0360 == NULL) return -1;

    device->data = (void *)hm0360;

    if (bsp_hm0360_open(conf))
        goto error;

    struct pi_cpi_conf cpi_conf;
    pi_cpi_conf_init(&cpi_conf);
    cpi_conf.itf = conf->cpi_itf;
    pi_open_from_conf(&hm0360->cpi_device, &cpi_conf);

    if (pi_cpi_open(&hm0360->cpi_device))
        goto error;

    struct pi_i2c_conf i2c_conf;
    pi_i2c_conf_init(&i2c_conf);
    i2c_conf.cs = 0x24 << 1; 
    i2c_conf.itf = conf->i2c_itf;
    pi_open_from_conf(&hm0360->i2c_device, &i2c_conf);

    if (pi_i2c_open(&hm0360->i2c_device))
        goto error2;

    pi_cpi_set_format(&hm0360->cpi_device, PI_CPI_FORMAT_BYPASS_BIGEND);

    hm0360->is_awake = 0;


    /* Opening XSHUTDOWN gpio */
    struct pi_gpio_conf gpio_conf;
    pi_gpio_conf_init(&gpio_conf);

    struct pi_device gpio_port;
    pi_open_from_conf(&gpio_port, &gpio_conf);

    if (pi_gpio_open(&gpio_port))
    {
        goto error;
    }

    uint32_t gpio_xshdown = conf->gpio_xshdown;
    uint32_t gpio_xsleep = conf->gpio_xsleep;

    /* configure it to 1 - powered up */
    pi_gpio_pin_configure(&gpio_port, gpio_xshdown, PI_GPIO_OUTPUT);
    pi_gpio_pin_configure(&gpio_port, gpio_xsleep, PI_GPIO_OUTPUT);
    pi_gpio_pin_write(&gpio_port, gpio_xshdown, 1);
    /* According to datasheet, need at least 200 us after power up */
    pi_time_wait_us(500);
    pi_gpio_pin_write(&gpio_port, gpio_xsleep, 1);

    printf("[HM0360] Reseting...\n");
    __hm0360_reset(hm0360);

    printf("[HM0360] Initializing regs...\n");
    __hm0360_init_regs(hm0360);

    return 0;

error2:
    pi_cpi_close(&hm0360->cpi_device);
error:
    pmsis_l2_malloc_free(hm0360, sizeof(hm0360_t));
    return -1;
}



static void __hm0360_close(struct pi_device *device)
{
    hm0360_t *hm0360 = (hm0360_t *)device->data;
    __hm0360_standby(hm0360);
    pi_cpi_close(&hm0360->cpi_device);
    pmsis_l2_malloc_free(hm0360, sizeof(hm0360_t));
}



static int32_t __hm0360_control(struct pi_device *device, pi_camera_cmd_e cmd, void *arg)
{
    int irq = disable_irq();

    hm0360_t *hm0360 = (hm0360_t *)device->data;

    switch (cmd)
    {
        case PI_CAMERA_CMD_ON:
            __hm0360_wakeup(hm0360);
            break;

        case PI_CAMERA_CMD_OFF:
            __hm0360_standby(hm0360);
            break;

        case PI_CAMERA_CMD_START:
            pi_cpi_control_start(&hm0360->cpi_device);
            __hm0360_wakeup(hm0360);
            break;

        case PI_CAMERA_CMD_STOP:
            __hm0360_standby(hm0360);
            pi_cpi_control_stop(&hm0360->cpi_device);
            break;

        default:
            break;
    }

    restore_irq(irq);

    return 0;
}



void __hm0360_capture_async(struct pi_device *device, void *buffer, uint32_t bufferlen, pi_task_t *task)
{
    hm0360_t *hm0360 = (hm0360_t *)device->data;

    pi_cpi_capture_async(&hm0360->cpi_device, buffer, bufferlen, task);
}



int32_t __hm0360_reg_set(struct pi_device *device, uint32_t addr, uint8_t *value)
{
    hm0360_t *hm0360 = (hm0360_t *)device->data;
    __hm0360_reg_write(hm0360, addr, *value);
    return 0;
}



int32_t __hm0360_reg_get(struct pi_device *device, uint32_t addr, uint8_t *value)
{
    hm0360_t *hm0360 = (hm0360_t *)device->data;
    *value = __hm0360_reg_read(hm0360, addr);
    return 0;
}



static pi_camera_api_t hm0360_api =
{
    .open           = &__hm0360_open,
    .close          = &__hm0360_close,
    .control        = &__hm0360_control,
    .capture_async  = &__hm0360_capture_async,
    .reg_set        = &__hm0360_reg_set,
    .reg_get        = &__hm0360_reg_get
};



void pi_hm0360_conf_init(struct pi_hm0360_conf *conf)
{
    conf->camera.api = &hm0360_api;
    conf->skip_pads_config = 0;
    bsp_hm0360_conf_init(conf);
    __camera_conf_init(&conf->camera);
}
