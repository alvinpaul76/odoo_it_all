#!/bin/bash

echo "Downloading External Modules..."

# Define file information as file_id:filename pairs
declare -A files=(
    ["1Disn9f0VKNlpuV5kAgcWQl4rF5zD7IO2"]="muk_web_theme-18.0.1.2.4.zip"
    ["16Yo0x6gEWILaxJGUsx0kzYv-iV4F0f5g"]="om_account_accountant-18.0.1.0.3.zip"
    ["18AmWcqiuYZnscyNdkE9gJI6PiY8pokw5"]="disable_debug_mode.zip"
    ["13IciLbbFPYdkYyG7fsTGSq8cdIgL4AtN"]="hr_employee_limit.zip"
    ["1a-K42QywtCvh5GNKTp7f6MwEw63zJvMB"]="res_user_limit.zip"
    ["1RRD4idbtorStjRZB6qkzLh7a_Cssum3k"]="disable_odoo_online-18.0.1.0.0.zip"
    ["19LL7BTE100IhudU0mHKdk3Y1_f7bPFcO"]="hr_expense_claim_auto_scan.zip"
    # Add more files as needed in the format ["file_id"]="filename"
)

# Download each file
for fileid in "${!files[@]}"; do
    filename="${files[$fileid]}"
    echo "Downloading ${filename}"
    curl -L -o "${filename}" "https://drive.google.com/uc?export=download&id=${fileid}"
    unzip -o -q "${filename}"
    rm "${filename}"
done

echo "All downloads completed"