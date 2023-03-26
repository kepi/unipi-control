from typing import Final

EVOK_MODEL_CONTENT: Final[
    str
] = """---
type: M103
modbus_register_blocks:
    - board_index : 1
      start_reg   : 0
      count       : 2
      frequency   : 1
    - board_index : 1
      start_reg   : 2
      count       : 3
      frequency   : 10
    - board_index : 1
      start_reg   : 5
      count       : 16
      frequency   : 1
    - board_index : 1
      start_reg   : 1000
      count       : 32
      frequency   : 5
    - board_index : 2
      start_reg   : 100
      count       : 19
      frequency   : 1
    - board_index : 2
      start_reg   : 1100
      count       : 21
      frequency   : 5
modbus_features:
    - type        : AO
      count       : 1
      major_group : 1
      modes       :
        - Voltage
        - Current
        - Resistance
      min_v       : 0
      max_v       : 10
      min_c       : 0
      max_c       : 0.020
      min_r       : 0
      max_r       : 2000
      val_reg     : 2
      res_val_reg : 4
      cal_reg     : 1024
      mode_reg    : 1019
    - type        : AI
      count       : 1
      major_group : 1
      modes       :
        - Voltage
        - Current
      tolerances  : brain
      min_v       : 0
      max_v       : 10
      min_c       : 0
      max_c       : 0.020
      val_reg     : 3
      cal_reg     : 1024 
      mode_reg    : 1024      
    - type        : DO
      count       : 4
      major_group : 1
      modes       :
        - Simple
        - PWM
      val_reg     : 1
      val_coil    : 0
      pwm_reg     : 16
      pwm_ps_reg  : 1017
      pwm_c_reg   : 1018
    - type        : DI
      count       : 4
      major_group : 1
      modes       :
        - Simple
        - DirectSwitch
      ds_modes    :
        - Simple
        - Inverted
        - Toggle
      min_v       : 5
      max_v       : 24
      val_reg     : 0
      counter_reg : 8
      direct_reg  : 1014
      deboun_reg  : 1010
      polar_reg   : 1015
      toggle_reg  : 1016
    - type        : UART
      major_group : 1
      parity_modes :
        - None
        - Odd
        - Even
      speed_modes :
        - 2400bps
        - 4800bps
        - 9600bps
        - 19200bps
        - 38400bps
        - 57600bps
        - 115200bps
      stopb_modes :
        - One
        - Two
      count       : 1
      conf_reg    : 1031
    - type        : LED
      major_group : 1
      count       : 4
      val_coil    : 8
      val_reg     : 20
    - type        : WD
      major_group : 1
      count       : 1
      val_reg     : 6
      timeout_reg : 1008
      nv_sav_coil : 1003
      reset_coil  : 1002
    - type        : REGISTER
      major_group : 1
      count       : 21
      start_reg   : 0
    - type        : REGISTER
      major_group : 1
      count       : 32
      start_reg   : 1000
    - type        : DI
      count       : 8
      major_group : 2
      modes       :
        - Simple
        - DirectSwitch
      ds_modes    :
        - Simple
        - Inverted
        - Toggle
      min_v       : 5
      max_v       : 24
      val_reg     : 100
      counter_reg : 103
      direct_reg  : 1118
      deboun_reg  : 1110
      polar_reg   : 1119
      toggle_reg  : 1120
    - type        : RO
      major_group : 2
      count       : 8
      val_reg     : 101
      val_coil    : 100
      modes       :
        - Simple
    - type        : WD
      count       : 1
      major_group : 2
      val_reg     : 102
      timeout_reg : 1108
      nv_sav_coil : 1103
      reset_coil  : 1102
    - type        : REGISTER
      major_group : 2
      count       : 19
      start_reg   : 100
    - type        : REGISTER
      major_group : 2
      count       : 21
      start_reg   : 1100
"""

INVALID_EVOK_MODEL_CONTENT: Final[
    str
] = """- board_index : 1
  start_reg   : 0
"""

CONVERTED_MODEL_CONTENT: Final[
    str
] = """modbus_features:
  - count: 4
    feature_type: DO
    major_group: 1
    val_reg: 1
  - count: 4
    feature_type: DI
    major_group: 1
    val_reg: 0
  - count: 4
    feature_type: LED
    major_group: 1
    val_coil: 8
    val_reg: 20
  - count: 8
    feature_type: DI
    major_group: 2
    val_reg: 100
  - count: 8
    feature_type: RO
    major_group: 2
    val_coil: 100
    val_reg: 101
modbus_register_blocks:
  - count: 2
    slave: 1
    start_reg: 0
  - count: 3
    slave: 1
    start_reg: 2
  - count: 16
    slave: 1
    start_reg: 5
  - count: 32
    slave: 1
    start_reg: 1000
  - count: 19
    slave: 2
    start_reg: 100
  - count: 21
    slave: 2
    start_reg: 1100
"""
