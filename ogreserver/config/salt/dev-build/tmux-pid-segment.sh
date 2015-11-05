# print the current {{ component_name }} pid

run_segment() {
	# check any pid files exist
	if ! ls /tmp/{{ app_name }}-{{ component_name }}*.pid &> /dev/null; then
		echo "DEAD"
		return 0
	fi

	# print the current {{ component_name }} pid
	cat /tmp/{{ app_name }}-{{ component_name }}*.pid | awk -vORS=, '{print}' | sed 's/,$/\n/'

	if [ $? == 1 ]; then
		echo "DEAD"
		return 0
	fi

	return 0
}
