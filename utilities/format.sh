latexindent -s -w -l format.yaml -c=build_files/ -m bylaws.tex Sections/*.tex Sections/Exec\ Portfolios/*.tex

if [ $# -gt 0 ]; then
  git restore bylaws.pdf
fi
