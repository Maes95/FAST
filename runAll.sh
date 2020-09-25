#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'STR' 'I-TSD')
algorithms=('FAST-one' 'FAST-pw' 'FAST-time')
projects=('kurento_v0' 'chart_v0' 'closure_v0'  'lang_v0'  'time_v0' 'math_v0' )
#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'FAST-time-mem')

it=10

for proj in "${projects[@]}"
do
    for alg in "${algorithms[@]}"
    do
        echo "Run $proj $alg $it"
        python py/prioritize.py $proj bbox $alg $it >> output/_logs/${proj}-${alg}-${it}_out.txt 2>&1 &
    done
done

# python py/prioritize.py chart_v0 bbox FAST-time 10