#! /bin/bash

rm -f "B00*.azw"
echo 'Cleaned up existing AZW books in /tmp'

NUM_BOOKS=$(find ~/Library/Containers/com.amazon.Kindle/Data/Library/Application\ Support/Kindle/My\ Kindle\ Content -name "B00*.azw" | wc -l | tr -d ' ')

if [[ $NUM_BOOKS -eq 0 ]]; then
	echo "You will need a DRM'd book in your Kindle downloads"
	exit 1
fi

echo "Found $NUM_BOOKS books in Kindle directory"
i=0

for F in ~/Library/Containers/com.amazon.Kindle/Data/Library/Application\ Support/Kindle/My\ Kindle\ Content/B00*.azw; do
	cp "$F" /tmp/DRM.azw
	echo "Copied ${F##*/} to DRM.azw"

	# only copy a single book
	break
done

echo 'Done'
