# I-J. Out of sample and decision

| | TRAIN | VALIDATION |
|---|---|---|
| G1 KNOWN vs UNKNOWN, primary target | 60.3 % (N 380) vs 41.9 % (N 310): +18.3 pts [+8.5, +26.3], p 2.27e-06 | 61.2 % (N 227) vs 33.6 % (N 253): +27.6 pts [+16.4, +38.4], p 1.95e-09 |
| within operators (Mantel-Haenszel) | +8.1 pts [-9.2, +18.4] | +20.0 pts [+6.3, +38.5] |
| matched | +5.1 pts [-8.8, +14.5] | +15.9 pts [-4.2, +32.9] |
| primary strategy on KNOWN, mean net | -15.0 % [-19.1, -12.1] (N 362) | -17.3 % [-21.3, -13.0] (N 220) |

Log loss, Model 3 minus Model 1, VALIDATION: -0.0023 [-0.0121, +0.0084].

**Decision (rule of analysis_plan.md section 7): NO INCREMENTAL SIGNAL**
