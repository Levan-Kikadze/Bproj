# Upload Error Test Cases

These files are intentionally broken or suspicious so you can test the dashboard's upload handling with realistic bad inputs.

## Files and Expected Behavior

- `empty_file.csv`: zero-byte file. Expected result: the app should report that the uploaded file is empty.
- `header_only.csv`: headers with no data rows. Expected result: the app should warn that the file has headers but no data rows.
- `duplicate_headers.csv`: duplicate `revenue` headers. Expected result: the app should block the upload and ask for unique header names.
- `blank_header.csv`: one blank header cell. Expected result: the app should block the upload and ask you to fill in every header name.
- `wrong_delimiter_semicolon.csv`: semicolon-separated file instead of comma-separated. Expected result: the app should explain that the file is not comma-separated.
- `single_column_only.csv`: parses into only one column. Expected result: the app should explain that the dashboard needs at least a date column and a revenue column.
- `malformed_quotes.csv`: broken quoting that should trigger a CSV parser error. Expected result: the app should say that the rows are malformed.
- `missing_date_column.csv`: readable file with revenue but no date-like column name. Expected result: the app should warn that no obvious date-like column was detected.
- `all_invalid_rows.csv`: has `date` and `revenue` headers, but every row should be removed during cleaning. Expected result: the app should reach the mapping stage, then explain that no usable rows remain after cleaning.

## Recommended Manual Check Order

1. Upload `empty_file.csv`.
2. Upload `wrong_delimiter_semicolon.csv`.
3. Upload `duplicate_headers.csv`.
4. Upload `blank_header.csv`.
5. Upload `malformed_quotes.csv`.
6. Upload `single_column_only.csv`.
7. Upload `missing_date_column.csv` and inspect the mapping warnings.
8. Upload `all_invalid_rows.csv` and keep the default mapping to test the post-cleaning error path.
