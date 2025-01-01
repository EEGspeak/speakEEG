# SpeakEEG Code Repository
### ***Rishabh Shah & Aaroosh Balakrishnan***

***

## File navigation
All files are separated into 3 main folders:
* **AV**: all audio/visual components used in project files (e.g. N170 images, P300 oddball "beep" noise)
* **DATA**: mainly CSV-formatted data files collected throughout algorithm testing. Separated into subdirectories labeled with headset name/software. Each headset subdirectory is then separated into specific test categories (e.g. Visual N170, Visual P300). `DATA/neurosity/` includes the `datasets/` folder, including other online datasets we used in our algorithm testing.
  * The data we use in our final algorithm will be sourced from our own algorithm, hosted on Neurofusion's website, however.
* **NOTEBOOKS**: the bulk of our code; it includes all of our classification and data collection algorithms. These can be found in `NOTEBOOKS/ANALYSIS/`. `NOTEBOOKS/eeg_notebooks/` includes files from [`NeuroTechX/EEG-ExPy`](https://github.com/NeuroTechX/EEG-ExPy).
  * **AAC**: the code module including a next-word prediction algorithm to update the SpeakEEG communication board. Also contains a CSV-stored board module. More documentation available in the module's files.
  * **TODO**: organize `NOTEBOOKS/ANALYSIS/` files and remove older versions.

Some files are omitted for privacy purposes. These files are mainly placeholder image files used in some of our testing and other miscellaneous deprecated files.

*Update 12/25/24*: Any CSV files marked with an `X_` at the begin signify a low quality recording, likely for software testing purposes, and are not intended to be used in training an algorithm.