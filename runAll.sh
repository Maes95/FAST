#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'STR' 'I-TSD')
algorithms=('FAST-time')
#projects=('kurento_v0' 'chart_v0' 'closure_v0'  'lang_v0'  'time_v0' 'math_v0' )
projects=('kurento_v0' 'chart_v0' 'closure_v0'  'lang_v0'  'time_v0' 'math_v0' 'mockito_v0' 'csv_v0' 'databind_v0' 'jsoup_v0' 'jxpath_v0' )
#algorithms=('FAST-one' 'FAST-pw' 'FAST-time' 'FAST-time-mem')
iterations=( 100 500 1000 )

run_prioritization() {
  proj=$1
  alg=$2
  it=$3
  echo "Running $proj $alg $it"
  python2 py/prioritize.py $proj bbox $alg $it >> output/_logs/${proj}-${alg}-${it}_out.txt 2>&1
  echo "Finish $proj $alg $it"
}

for it in "${iterations[@]}"
do
  for proj in "${projects[@]}"
  do
      for alg in "${algorithms[@]}"
      do
          run_prioritization $proj $alg $it &
      done
  done
  sleep 2
done

wait

echo "Generate merge-chart of pareto frontiers"

for proj in "${projects[@]}"
do
    python2 py/MergeParetoFrontiers.py $proj
done

# python py/prioritize.py kurento_v0 bbox FAST-time 100