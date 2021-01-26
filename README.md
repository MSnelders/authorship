# authorship
A little script to wrangle CHIME/FRB author lists

Here is a Google Sheets template you can use for authors to sign up:
https://docs.google.com/spreadsheets/d/1AJSt2wNmhyU-DhWLPmaiFRoPkTuKINc68Ij4x937EKg/edit

When you are ready, open each of the two sheets (Authors and
Affiliations), and go to File->Download->Tab Separated Values and save the two TSV files.

Then run
```
python3 authors.py authors.tsv affils.tsv > auth.tex
```

For a demo of what it will look like, run
```
pdflatex apj
pdflatex apj
```

