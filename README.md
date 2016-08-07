# Objective
The intent of this repo is to demonstrate what relatively high-quality code to
solve a provided, specific problem looks like in various languages.
# Statement of problem
Given a set of many `x,y` points (for example those in
`test_data/coordinates.csv`), find all of the points within radius `r` of a
given centroid or set of centroids.  Also, be able to search for the radius `r`
which makes a given percentage of the coordinates fall within `r` of at least
one centroid.
## Implementation
The implementation is with a quad tree.  The objective is for the algorithm to
be as similar across languages as is practical.
