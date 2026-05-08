#!/bin/bash
set -euo pipefail

# Auto-generated Phase 2M collar job runner.

echo 'Running phase2m_collar_000_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_000 --K-lo 0.9600001 --K-hi 0.9605001999999999 --K-mid 0.9602501 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_000_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_000_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_000 --K-lo 0.9600001 --K-hi 0.9605001999999999 --K-mid 0.9602501 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_000_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_001_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_001 --K-lo 0.9605 --K-hi 0.9610001999999999 --K-mid 0.9607500999999999 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_001_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_001_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_001 --K-lo 0.9605 --K-hi 0.9610001999999999 --K-mid 0.9607500999999999 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_001_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_002_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_002 --K-lo 0.961 --K-hi 0.9615001999999998 --K-mid 0.9612500999999999 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_002_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_002_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_002 --K-lo 0.961 --K-hi 0.9615001999999998 --K-mid 0.9612500999999999 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_002_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_003_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_003 --K-lo 0.9614999999999999 --K-hi 0.9620001999999997 --K-mid 0.9617500999999998 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_003_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_003_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_003 --K-lo 0.9614999999999999 --K-hi 0.9620001999999997 --K-mid 0.9617500999999998 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_003_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_004_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_004 --K-lo 0.9619999999999999 --K-hi 0.9625001999999997 --K-mid 0.9622500999999998 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_004_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_004_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_004 --K-lo 0.9619999999999999 --K-hi 0.9625001999999997 --K-mid 0.9622500999999998 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_004_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_005_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_005 --K-lo 0.9624999999999998 --K-hi 0.9630001999999996 --K-mid 0.9627500999999997 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_005_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_005_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_005 --K-lo 0.9624999999999998 --K-hi 0.9630001999999996 --K-mid 0.9627500999999997 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_005_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_006_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_006 --K-lo 0.9629999999999997 --K-hi 0.9635001999999996 --K-mid 0.9632500999999997 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_006_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_006_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_006 --K-lo 0.9629999999999997 --K-hi 0.9635001999999996 --K-mid 0.9632500999999997 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_006_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_007_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_007 --K-lo 0.9634999999999997 --K-hi 0.9640001999999995 --K-mid 0.9637500999999996 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_007_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_007_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_007 --K-lo 0.9634999999999997 --K-hi 0.9640001999999995 --K-mid 0.9637500999999996 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_007_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_008_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_008 --K-lo 0.9639999999999996 --K-hi 0.9645001999999995 --K-mid 0.9642500999999996 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_008_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_008_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_008 --K-lo 0.9639999999999996 --K-hi 0.9645001999999995 --K-mid 0.9642500999999996 --N-values 1024,1536,2048,3072,4096 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 2400.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_008_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_009_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_009 --K-lo 0.9644999999999996 --K-hi 0.9650001999999994 --K-mid 0.9647500999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_009_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_009_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_009 --K-lo 0.9644999999999996 --K-hi 0.9650001999999994 --K-mid 0.9647500999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_009_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_009_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_009 --K-lo 0.9644999999999996 --K-hi 0.9650001999999994 --K-mid 0.9647500999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_009_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_010_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_010 --K-lo 0.9649999999999995 --K-hi 0.9655001999999994 --K-mid 0.9652500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_010_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_010_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_010 --K-lo 0.9649999999999995 --K-hi 0.9655001999999994 --K-mid 0.9652500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_010_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_010_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_010 --K-lo 0.9649999999999995 --K-hi 0.9655001999999994 --K-mid 0.9652500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_010_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_011_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_011 --K-lo 0.9654999999999995 --K-hi 0.9660001999999993 --K-mid 0.9657500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_011_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_011_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_011 --K-lo 0.9654999999999995 --K-hi 0.9660001999999993 --K-mid 0.9657500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_011_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_011_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_011 --K-lo 0.9654999999999995 --K-hi 0.9660001999999993 --K-mid 0.9657500999999994 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_011_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_012_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_012 --K-lo 0.9659999999999994 --K-hi 0.9665001999999993 --K-mid 0.9662500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_012_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_012_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_012 --K-lo 0.9659999999999994 --K-hi 0.9665001999999993 --K-mid 0.9662500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_012_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_012_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_012 --K-lo 0.9659999999999994 --K-hi 0.9665001999999993 --K-mid 0.9662500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_012_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_013_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_013 --K-lo 0.9664999999999994 --K-hi 0.9670001999999992 --K-mid 0.9667500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_013_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_013_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_013 --K-lo 0.9664999999999994 --K-hi 0.9670001999999992 --K-mid 0.9667500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_013_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_013_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_013 --K-lo 0.9664999999999994 --K-hi 0.9670001999999992 --K-mid 0.9667500999999993 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_013_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_014_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_014 --K-lo 0.9669999999999993 --K-hi 0.9675001999999991 --K-mid 0.9672500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_014_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_014_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_014 --K-lo 0.9669999999999993 --K-hi 0.9675001999999991 --K-mid 0.9672500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_014_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_014_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_014 --K-lo 0.9669999999999993 --K-hi 0.9675001999999991 --K-mid 0.9672500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_014_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_015_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_015 --K-lo 0.9674999999999992 --K-hi 0.9680001999999991 --K-mid 0.9677500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_015_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_015_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_015 --K-lo 0.9674999999999992 --K-hi 0.9680001999999991 --K-mid 0.9677500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_015_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_015_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_015 --K-lo 0.9674999999999992 --K-hi 0.9680001999999991 --K-mid 0.9677500999999992 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_015_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_016_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_016 --K-lo 0.9679999999999992 --K-hi 0.968500199999999 --K-mid 0.9682500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_016_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_016_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_016 --K-lo 0.9679999999999992 --K-hi 0.968500199999999 --K-mid 0.9682500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_016_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_016_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_016 --K-lo 0.9679999999999992 --K-hi 0.968500199999999 --K-mid 0.9682500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_016_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_017_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_017 --K-lo 0.9684999999999991 --K-hi 0.969000199999999 --K-mid 0.9687500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_017_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_017_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_017 --K-lo 0.9684999999999991 --K-hi 0.969000199999999 --K-mid 0.9687500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_017_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_017_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_017 --K-lo 0.9684999999999991 --K-hi 0.969000199999999 --K-mid 0.9687500999999991 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_017_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_018_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_018 --K-lo 0.9689999999999991 --K-hi 0.9695001999999989 --K-mid 0.969250099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_018_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_018_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_018 --K-lo 0.9689999999999991 --K-hi 0.9695001999999989 --K-mid 0.969250099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_018_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_018_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_018 --K-lo 0.9689999999999991 --K-hi 0.9695001999999989 --K-mid 0.969250099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_018_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_019_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_019 --K-lo 0.969499999999999 --K-hi 0.9700001999999989 --K-mid 0.969750099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_019_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_019_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_019 --K-lo 0.969499999999999 --K-hi 0.9700001999999989 --K-mid 0.969750099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_019_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_019_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_019 --K-lo 0.969499999999999 --K-hi 0.9700001999999989 --K-mid 0.969750099999999 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_019_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_020_os64_sg0p00025'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_020 --K-lo 0.969999999999999 --K-hi 0.9700002 --K-mid 0.9700000999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.00025 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_020_os64_sg0p00025_candidate.json

echo 'Running phase2m_collar_020_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_020 --K-lo 0.969999999999999 --K-hi 0.9700002 --K-mid 0.9700000999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_020_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_020_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_020 --K-lo 0.969999999999999 --K-hi 0.9700002 --K-mid 0.9700000999999995 --N-values 1024,2048,4096,6144 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 3600.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_020_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_021_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_021 --K-lo 0.9700000000000001 --K-hi 0.9702002 --K-mid 0.9701001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_021_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_021_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_021 --K-lo 0.9700000000000001 --K-hi 0.9702002 --K-mid 0.9701001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_021_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_021_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_021 --K-lo 0.9700000000000001 --K-hi 0.9702002 --K-mid 0.9701001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_021_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_022_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_022 --K-lo 0.9702000000000001 --K-hi 0.9704001999999999 --K-mid 0.9703001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_022_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_022_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_022 --K-lo 0.9702000000000001 --K-hi 0.9704001999999999 --K-mid 0.9703001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_022_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_022_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_022 --K-lo 0.9702000000000001 --K-hi 0.9704001999999999 --K-mid 0.9703001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_022_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_023_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_023 --K-lo 0.9704 --K-hi 0.9706001999999999 --K-mid 0.9705001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_023_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_023_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_023 --K-lo 0.9704 --K-hi 0.9706001999999999 --K-mid 0.9705001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_023_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_023_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_023 --K-lo 0.9704 --K-hi 0.9706001999999999 --K-mid 0.9705001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_023_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_024_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_024 --K-lo 0.9706 --K-hi 0.9708001999999999 --K-mid 0.9707001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_024_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_024_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_024 --K-lo 0.9706 --K-hi 0.9708001999999999 --K-mid 0.9707001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_024_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_024_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_024 --K-lo 0.9706 --K-hi 0.9708001999999999 --K-mid 0.9707001 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_024_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_025_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_025 --K-lo 0.9708 --K-hi 0.9710001999999999 --K-mid 0.9709000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_025_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_025_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_025 --K-lo 0.9708 --K-hi 0.9710001999999999 --K-mid 0.9709000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_025_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_025_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_025 --K-lo 0.9708 --K-hi 0.9710001999999999 --K-mid 0.9709000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_025_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_026_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_026 --K-lo 0.971 --K-hi 0.9712001999999998 --K-mid 0.9711000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_026_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_026_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_026 --K-lo 0.971 --K-hi 0.9712001999999998 --K-mid 0.9711000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_026_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_026_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_026 --K-lo 0.971 --K-hi 0.9712001999999998 --K-mid 0.9711000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_026_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_027_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_027 --K-lo 0.9712 --K-hi 0.9714001999999998 --K-mid 0.9713000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_027_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_027_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_027 --K-lo 0.9712 --K-hi 0.9714001999999998 --K-mid 0.9713000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_027_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_027_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_027 --K-lo 0.9712 --K-hi 0.9714001999999998 --K-mid 0.9713000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_027_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_028_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_028 --K-lo 0.9713999999999999 --K-hi 0.9716001999999998 --K-mid 0.9715000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_028_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_028_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_028 --K-lo 0.9713999999999999 --K-hi 0.9716001999999998 --K-mid 0.9715000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_028_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_028_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_028 --K-lo 0.9713999999999999 --K-hi 0.9716001999999998 --K-mid 0.9715000999999999 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_028_os64_sg2p5em05_candidate.json

echo 'Running phase2m_collar_029_os64_sg0p0001'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_029 --K-lo 0.9715999999999999 --K-hi 0.971636 --K-mid 0.97161805 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 0.0001 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_029_os64_sg0p0001_candidate.json

echo 'Running phase2m_collar_029_os64_sg5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_029 --K-lo 0.9715999999999999 --K-hi 0.971636 --K-mid 0.97161805 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_029_os64_sg5em05_candidate.json

echo 'Running phase2m_collar_029_os64_sg2p5em05'
/pscratch/sd/s/suryact/phase2k_venv/bin/python scripts/audit/run_lower_anchor_phase2g_segment.py --segment-id phase2m_collar_029 --K-lo 0.9715999999999999 --K-hi 0.971636 --K-mid 0.97161805 --N-values 2048,4096,6144,8192 --oversample-factor 64 --sigma-cap 2.5e-05 --max-wall-seconds 4800.0 --out-dir artifacts/proof_audit/lower_corridor/phase2m_collar --table-dir tables/proof_audit/lower_corridor/phase2m_collar --candidate-name phase2m_collar_029_os64_sg2p5em05_candidate.json
