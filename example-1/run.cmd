@echo off

set graphviz="c:\Program files\Graphviz\bin\dot.exe"

if exist f.dot del f.dot
if exist f.err del f.err
if exist result.err del result.err
if exist result.png del result.png
if exist result.svg del result.svg

dna-multi-match.py family.ged --show --testers 1,1000 11,2000 21,400 >f.dot 2>f.err

%graphviz% -Tpng f.dot -o result.png 2>result.err
%graphviz% -Tsvg f.dot -o result.svg