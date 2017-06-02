#!/bin/sh
DOMAIN=nautilus-git
BASEDIR=$(dirname $0)
OUTPUT_FILE=${BASEDIR}/po/${DOMAIN}.pot

echo "Extracting translatable strings... "

find ${BASEDIR}/ -name '*.py' | xgettext \
  --output $OUTPUT_FILE \
  --files-from=- \
  --directory=$BASEDIR \
  --language=Python \
  --keyword=C_:1c,2 \
  --from-code=utf-8

find ${BASEDIR}/ -name '*.ui' | xgettext \
  --output $OUTPUT_FILE \
  --join-existing \
  --files-from=- \
  --directory=$BASEDIR \
  --language=Glade \
  --foreign-user \
  --keyword=C_:1c,2 \
  --from-code=utf-8


xgettext \
  --join-existing \
  --output $OUTPUT_FILE \
  --default-domain=$DOMAIN \
  --package-name=$DOMAIN \
  --directory=$BASEDIR \
  --foreign-user \
  --language=appdata \
  ${BASEDIR}/data/nautilus-git.metainfo.xml.in

# Merge the messages with existing po files
po_files=$(find ${BASEDIR}/po/ -name "*.po")
if [ ${#po_files[@]} != 0 ]; then
  echo "Merging with existing translations..."
  for file in $po_files
  do
    echo -n $file
    msgmerge --update $file $OUTPUT_FILE
  done
fi
