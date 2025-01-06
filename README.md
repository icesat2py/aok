# aok
ATLAS Ocean Kd (AOK) - calculating ocean Kd values using ICESat-2

> [!WARNING]
> This package is currently under active development to produce the most reliable calculations of Kd values.
> The code is therefore unstable, may have significant uncertainties, and should be used with caution.
> This repository contains Python code developed in collaboration to replicate the functionality of the original MATLAB scripts (https://github.com/emilyeidam/icesat-2_kdph
) by Dr. Emily Eidam (emily.eidam@oregonstate.edu). The code facilitates processing ICESat-2 data to calculate the diffuse attenuation coefficient (Kd) based on space-based lidar photon profiles, following methods described in the original MATLAB code. Please cite appropriately both Python and the MATLAB version under the GNU GPLv3 license (can you check which one is better @Jessica) if you use this code in your research.

[![All Contributors](https://img.shields.io/github/all-contributors/icesat2py/aok?color=ee8449&style=flat-square)](#contributors)

# Quickstart

# Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/ChaoEcohydroRS/icesat-2_kdph_py.git
   cd IS2_Kd_Proj


2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure .h5 files are placed in the appropriate default folder structure.

# Usage
1. Edit the config.py file to set up file paths and any parameters.
2. Run the entire workflow through main.py:

   ```bash
   python main.py
   ```

# Contributing

[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](code_of_conduct.md) 

Our team follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org), version 2.1, available at
[https://www.contributor-covenant.org/version/2/1/code_of_conduct.html](https://www.contributor-covenant.org/version/2/1/code_of_conduct.html).

## Team members

We encourage all active team members with repository access to work directly on their own branch, creating one branch for each "task" they are working on.
This makes it easy for others to access their work and to keep things updated.
If you are in need of a more personalized scratch space, please fork the repository to your personal GitHub account.

## Everyone

We welcome contributions from any user.
Some guidelines on [ways to contribute](https://icepyx.readthedocs.io/en/latest/contributing/contribution_guidelines.html) and [how to contribute](https://icepyx.readthedocs.io/en/latest/contributing/how_to_contribute.html) are available in the [icepyx](https://icepyx.readthedocs.io/en/latest/index.html) documentation.

## Recognizing Contributions
Our full attribution guidelines are coming soon.

We use the [All Contributors Specification](https://allcontributors.org/docs/en/specification)
to recognize our incredible [contributor team](CONTRIBUTORS.md).

# Citation
If you use this code, please cite:

Eidam, E.F., K. Bisson, C. Wang, C. Walker, and A. Gibbons (2024). ICESat-2 and ocean particulates: A roadmap for calculating Kd from space-based lidar photon profiles. Remote Sensing of Environment. Vol. 311. https://doi.org/10.1016/j.rse.2024.114222

# License
This project is licensed under the GNU GPLv3 license.


