# Berliner PV-Monitor

Analysis and visualization of photovoltaic installations in Berlin using data from Germany's Marktstammdatenregister (MaStR).

**View the Live Project:** <https://afanegas.github.io/berlin-pv-monitor/>

## Overview

This project imports, analyzes, and visualizes solar power installation data for Berlin, providing insights into the growth and distribution of photovoltaic systems in the city.

## Features

- Import solar installation data from MaStR
- Analyze yearly solar capacity growth
- Interactive web visualizations
- Historical data tracking

## Files

- `Import_MaStR.py` - Script to import data from the MaStR registry
- `Analysis_MaStR.py` - Data analysis and processing
- `index.html` - Main visualization page
- `methodology.html` - Documentation of data methodology
- `solar_berlin_yearly.csv` - Processed yearly data
- `master.sh` - Automation script

## Setup

```bash
pip install -r requirements.txt
```

## Usage

Run the master script to update data and generate visualizations:

```bash
./master.sh
```

Since the data import can take a long time, you can run it in the background:

```bash
nohup ./master.sh > logs/latest_run.log 2>&1 &
```
Or run individual components:

```bash
python Import_MaStR.py
python Analysis_MaStR.py
```

## License

MIT License - See [LICENSE](LICENSE) for details.

## Data Source

Data sourced from [Marktstammdatenregister (MaStR)](https://www.marktstammdatenregister.de/), Germany's register for energy market installations.

## Acknowledgments

Big thanks to [open-mastr](https://github.com/OpenEnergyPlatform/open-MaStR) for providing the tools and framework to access and process MaStR data efficiently.
