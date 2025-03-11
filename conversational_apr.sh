# cd /external_disk/coding_space/ChatRepairRegression
# python3 -m src.main conversational-apr \
#     --dataset regminer4apr \
#     --data-id 4 \
#     --input-dir /external_disk/coding_space/ChatRepairRegression/experiments/regminer4apr_function_level.json \
#     --mapping-dir /external_disk/coding_space/ChatRepairRegression/experiments/mapping.txt \
#     --output-dir /external_disk/coding_space/ChatRepairRegression/experiments/output \
#     --tmp-dir /external_disk/coding_space/ChatRepairRegression/experiments/tmp-conversation \
#     --env-dir /external_disk/coding_space/ChatRepairRegression/experiments/environments/regminer4apr \
#     --time-limit 1800 \
#     --attempts 20 \
#     --iterations 5 \
#     --model-name "gpt-3.5-turbo" \
#     --temperature 0.7 \
#     --top-p 0.95 \
#     --early-stop 

# =============== HUNK LEVEL ==================
# BUG_ID=(1 2 3 5 10 12 13 17 21 22 24 25 28 30 31 33 34 35 36 37 38 39 40 41 42 43 44 46 47 48 52 54 55 56 63 65 66 72 73 74 75 76 77 81 82 84 95)
# BUG_ID=(1 2 3 5 10 12 13 17 21 22 24 25 28 30 31 33 34 35 36 37 38 39 40) 
BUG_ID=(24 25)
# BUG_ID=(41 42 43 44 46 47 48 52 54 55 63 65 66 72 73 74 75 76 77 81 82 84 95)
# =============== FUNCTION LEVEL ==================
# BUG_ID=(4 11 15 16 18)
# BUG_ID=(26 50 59 62 64 69 70 71 78 83 85 94)
# BUG_ID=(4 83 85 94)
for i in "${BUG_ID[@]}";  
do
    echo "********************************************************************"
    
    cd /external_disk/coding_space/ChatRepairRegression
    python3 -m src.main conversational-apr \
        --dataset regminer4apr \
        --data-id "$i" \
        --input-dir /external_disk/coding_space/ChatRepairRegression/experiments/regminer4apr_function_level.json \
        --mapping-dir /external_disk/coding_space/ChatRepairRegression/experiments/mapping.txt \
        --output-dir /external_disk/coding_space/ChatRepairRegression/experiments/output \
        --tmp-dir /external_disk/coding_space/ChatRepairRegression/experiments/tmp-conversation \
        --env-dir /external_disk/coding_space/ChatRepairRegression/experiments/environments/regminer4apr \
        --time-limit 1800 \
        --attempts 20 \
        --iterations 5 \
        --model-name "gpt-4o" \
        --temperature 0.7 \
        --top-p 0.95 \
        --early-stop         

    echo "********************************************************************"
done