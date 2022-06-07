# EDist-ILP

A generic tool for computing the edit distance between strings that have different vocabularies using Integer Linear Programming (ILP).

This tool was used to compute transcription accuracy in this paper: [Decipherment of Historical Manuscript Images](https://ieeexplore.ieee.org/document/8978177)


## Dependencies
- Python 3
- [Gurobi Optimizer](http://www.gurobi.com)


## To run this code
`python edist-ilp.py <gold_file> <system_out_file>`
