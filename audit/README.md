# Analysis-file checksums and data-flow audit

This directory provides the public audit materials referenced in the manuscript's code and data availability statement.

## Files

- `file_checksums_sha256.csv`: SHA-256 checksums for the raw database and principal analysis/audit files.
- `data_flow_audit.csv`: record- and profile-level accounting from the original database through filtering and standard-depth harmonization.
- `depth_harmonization_audit.csv`: sample counts and SOC summaries under the 50%, 80%, and 100% standard-layer coverage thresholds.

## Key checks

- Original database: 23,103 layer records from 7,955 profiles.
- After removing 3,119 records with missing SOC and 40 records with SOC > 200 g kg-1: 19,944 records from 5,877 profiles.
- Layers crossing the 20, 50, or 100 cm boundaries: 9,446 (47.36%).
- Profiles excluded from thickness-weighted harmonization because of overlapping or indistinguishable parallel layers: 176.
- At the prespecified >=50% coverage threshold, the 0-20, 20-50, 50-100, and 100-200 cm intervals contain 5,668, 4,199, 3,607, and 515 records, respectively (13,989 total).

## SHA-256 verification

Run the following command in the project root after obtaining the corresponding files:

```bash
sha256sum SOCS_V10.csv
sha256sum data_raw/SOCS_V10_Readme.txt
sha256sum output_formal/audit_summary.json
sha256sum depth_harmonization/standard_depth_coverage_050.csv
sha256sum depth_harmonization/profile_interval_qa.csv
```

The output must match `file_checksums_sha256.csv`. A mismatch indicates that the file version differs from the one used for the reported analysis.

The source database is described in `DATA_AVAILABILITY.md`. Repository visibility alone makes these audit tables public; the raw database remains governed by its original license and repository record.
