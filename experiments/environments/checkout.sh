#!/bin/bash

PATH=$PATH:../bin
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64

# BUG_ID=(1 2 3 5 10 12 13 17 21 22 24 25 28 30 31 33 34 35 36 37 38 39 40 41 42 43 44 46 47 48 52 54 55 56 63 65 66 72 73 74 75 76 77 81 82 84 95)
# BUG_ID=(4 11 15 16 18 26 50 59 62 64 69 70 71 78 83 85 94)
# BUG_ID=(96 98 99)
BUG_ID=(100 101 102 103 104 105 106 107 108 109 111 112 113 114 115 117 118 120 121 122 123 124 125 126 127 128 129 130 131 134 135 136 137 138 139 140 143 144 145 146 147 148 150)

for i in "${BUG_ID[@]}"; 
do
    echo "***********************************************"
    regminer4apr checkout -rb "$i" -w ./regminer4apr
    # regminer4apr compile -w "../examples/RegressionBug-$i/BUGGY"
    # regminer4apr test -w "../examples/RegressionBug-$i/BUGGY"
    echo "***********************************************"
done
