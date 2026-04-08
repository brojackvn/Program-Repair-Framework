cd /external_disk/coding_space/ChatRepairRegression

# BUG_ID=(1 2 3 5 10 12 13 17 21 22 24 25 28 30 31 33 34 35 36 37 38 39 40 41 42 43 44 46 47 48 52 54 55 56 63 65 66 72 73 74 75 76 77 81 82 84 95)
# BUG_ID=(4 11 15 16 18 26 50 59 62 64 69 70 71 78 83 85 94 99)
# BUG_ID=(100 102 101 103 104 105 106 107 108 109 111 112 113 114 115 117 118 120 121 122 123 124)
# BUG_ID=(125 126 127 128 129 130 131 134 135 136 137 138 139 140 143 144 145 146 147 148 150)

# IDs that require Java 11
JAVA11_IDS=(100 110 144 145)

for i in "${BUG_ID[@]}";  
do
    echo "********************************************************************"
    # If id is 100, 110, 144, 145, 147, module load Java/11.0.18
    # else module load Java/1.8.0_241
    echo "Processing BUG_ID=$i"

    # Check if current ID is in JAVA11_IDS
    if [[ " ${JAVA11_IDS[@]} " =~ " ${i} " ]]; then
        echo "Loading Java 11..."
        export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
    else
        echo "Loading Java 8..."
        export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
    fi

    # Add selected Java
    export PATH=$JAVA_HOME/bin:$PATH

    PYTHONPATH=/external_disk/coding_space/ChatRepairRegression \
    python3 -m src.main conversational-apr-with-bic \
        --dataset regminer4apr \
        --data-id "$i" \
        --input-dir /external_disk/coding_space/ChatRepairRegression/experiments/regminer4apr-bug-metadata.json \
        --mapping-dir /external_disk/coding_space/ChatRepairRegression/experiments/mapping-regminer4apr.txt \
        --output-dir /external_disk/coding_space/ChatRepairRegression/experiments/test-output \
        --tmp-dir /external_disk/coding_space/ChatRepairRegression/experiments/tmp-conversation-bic \
        --env-dir /external_disk/coding_space/ChatRepairRegression/experiments/environments/regminer4apr \
        --time-limit 1800 \
        --attempts 10 \
        --iterations 5 \
        --model-name "gpt-4o" \
        --temperature 1 \
        --top-p 0.95 \
        --early-stop 

    echo "********************************************************************"
done