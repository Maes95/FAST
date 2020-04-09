projects=('kurento_v0')
#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'STR' 'I-TSD')
algorithms=('TIME-FAST' 'FAST-one' 'FAST-pw' 'FAST-time')

#projects=('chart_v0' 'closure_v0'  'lang_v0'  'time_v0' 'math_v0' )
#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'FAST-time-mem')

it=100

for proj in "${projects[@]}"
do
    for alg in "${algorithms[@]}"
    do
        echo "Run $proj $alg $it"
        python py/prioritize.py $proj bbox $alg $it
    done
done

# python py/prioritize.py chart_v0 bbox FAST-time 1 