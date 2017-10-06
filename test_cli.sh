#!/bin/bash

templatetester="python3 previewtemplate.py"

exit_code=0
for folder in test_files/*/; do
    echo "Testing folder ${folder}"
    if [ -f "${folder}/style.css" ]; then
        echo "Found css file"
        style="--style ${folder}/style.css"
    else
        echo "Warning: Did not find css file"
        style=""
    fi
    ${templatetester}  ${style} --output "${folder}/test.html" "${folder}/template.html" "${folder}/fields.txt" 
    if cmp -s "${folder}/test.html" "${folder}/output.html"; then
        echo "Output as expected"
    else
        echo "Outputs differ! Here is the full diff:"
        diff "${folder}/test.html" "${folder}/output.html"
        exit_code=1
    fi
    
    rm "${folder}/test.html"
    
done

exit ${exit_code}
