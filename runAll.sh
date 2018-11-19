projects=('chart_v0' 'closure_v0'  'lang_v0' 'math_v0' 'time_v0', 'fullteachingexperimente2e_v0')
algorithms=('FAST-one' 'FAST-pw' 'FAST-time')
it=50

for proj in "${projects[@]}"
do
    for alg in "${algorithms[@]}"
    do
        echo "Run $proj $alg $it"
        python py/prioritize.py $proj bbox $alg $it
    done
done