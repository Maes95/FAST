read -p "Do you want to overwrite the data in input folder? " -n 1 -r
echo    # (optional) move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    exit 1
fi

# Copy defects4j output to FAST input

cp -TR output/Lang/ ../input/lang_v0/
cp -TR output/Math/ ../input/math_v0/
cp -TR output/Chart/ ../input/chart_v0/
cp -TR output/Closure/ ../input/closure_v0/
cp -TR output/Time/ ../input/time_v0/
cp -TR output/Mockito/ ../input/mockito_v0/
cp -TR output/JxPath/ ../input/jxpath_v0/
cp -TR output/Csv/ ../input/csv_v0/
cp -TR output/Jsoup/ ../input/jsoup_v0/
cp -TR output/JacksonDatabind/ ../input/databind_v0/