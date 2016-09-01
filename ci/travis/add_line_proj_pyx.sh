#!/usr/bin/env bash
# adds this line to _proj.pyx to enable measuring Cython coverage
sed -i '1 i\# cython: linetrace=True' _proj.pyx
