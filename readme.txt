DARKNET PIPELINE + DASHBOARD: SETUP STEPS
CSI 4430 - Darknet project

WHAT YOU NEED
- Python 3.10 or newer
- Tableau Desktop Public Edition (free): https://www.tableau.com/students
- The project zip, and the files Darknet.csv and Darknet_test.csv

------------------------------------------------------------
PART 1: SET UP THE PROJECT FOLDER
------------------------------------------------------------
1. Unzip the project folder anywhere on your computer.

2. Inside the project folder, make sure there is a folder named "data"
   containing:
      data/Darknet.csv
      data/Darknet_test.csv
   If the "data" folder is missing, create it and copy both CSVs in.

3. Open a terminal INSIDE the project folder (the folder that contains
   analysis.py). The pipeline only works when run from this folder.

------------------------------------------------------------
PART 2: RUN THE PIPELINE
------------------------------------------------------------
   python analysis.py
   python test_pipeline.py

You should see:
- "Records before processing 150" (100 from Darknet.csv, 50 from
  Darknet_test.csv)
- "n = 150 events, 3,707 packets"
- Three lines that say PASSED


------------------------------------------------------------
PART 3: OPEN THE DASHBOARD
------------------------------------------------------------
1. Open the .twbx file in the "dashboard" folder with Tableau Desktop
   Public Edition. It opens right away with a saved copy of the data.

2. To connect it to YOUR pipeline output (so it updates when you rerun
   the pipeline):
   a. Click the "Data Source" tab (bottom left).
   b. Click the arrow next to "darknet_clean" > Edit Connection.
      Select: outputs/processed/darknet_clean.csv in your project folder.
   c. Do the same for "before_after_summary".
      Select: outputs/reports/before_after_summary.csv
   d. Menu: Data > Refresh (do this for each data source).

3. Check the dashboard:
   - source_file filter set to (All):        150 events, 3,707 packets
   - source_file filter set to Darknet.csv:  100 events, 2,255 packets

------------------------------------------------------------
HOW THE DASHBOARD CONNECTS TO THE PIPELINE
------------------------------------------------------------
Rerun "python analysis.py", then in Tableau choose Data > Refresh.
Every chart updates from the pipeline's output files.

