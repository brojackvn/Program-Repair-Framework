cd /external_disk/coding_space/ChatRepairRegression

# PANDAS
# BUG_ID=(1 2 3 4 5 6 8 9 11 12 14 16 17 18 19 20 21 22)
# # DJANGO
# BUG_ID=(15 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 43 44 45 46 48 49 50)

for i in "${BUG_ID[@]}";  
do
    echo "********************************************************************"
    echo "Processing BUG_ID=$i"

    # Add selected Java
    export PATH=$JAVA_HOME/bin:$PATH

    PYTHONPATH=/external_disk/coding_space/ChatRepairRegression \
    python3 -m src.main prompt-apr-with-bic \
        --dataset pyregression \
        --data-id "$i" \
        --input-dir /external_disk/coding_space/ChatRepairRegression/experiments/pyregression-bug-metadata.json \
        --mapping-dir /external_disk/coding_space/ChatRepairRegression/experiments/mapping-pyregression.txt \
        --output-dir /external_disk/coding_space/ChatRepairRegression/experiments/pyregression-output \
        --env-dir /external_disk/coding_space/ChatRepairRegression/experiments/environments/pyregression \
        --time-limit 720 \
        --sample-size 10 \
        --model-name "gpt-4o" \
        --temperature 1 \
        --top-p 0.95 \
        --early-stop    

    echo "********************************************************************"
done