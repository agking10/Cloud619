INPUT_DIR=./inputs
OUTPUT_DIR=./ecmp_results_new
INPUT_FILES='stag_prob_0_5_3_data'
# random0_datarandom0_bij_data hotspot_one_to_one_data all_to_all_data'
DURATION=50

for f in $INPUT_FILES;
do
        input_file=$INPUT_DIR/$f
        pref="fattree-ecmp"
        out_dir=$OUTPUT_DIR/$pref/$f
        sudo python ./mn_ft.py -i $input_file -d $out_dir -p 0.03 -t $DURATION --ecmp --iperf --bwlow 1.0 --bwhigh 10.0
        sudo mn -c
done
sudo python ../lib/clean.py
