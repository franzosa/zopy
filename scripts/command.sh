python heatmap_flex.py test.tsv \
       --output ~/Dropbox/temp.pdf \
       --lastcol Recruiter-type \
       --rowmeta Recruiter-type \
       --lastrow Random \
       --colmeta Random \
       --title "Test of the new heatmap system" \
       --special "cbar_extent:0.5|cbar_shift:1" \
       --wdesign "cbar:8|rowtree:3|heatmap:20|rowmeta:1|rownames:12|legend:8" \
       --hdesign "title:1|colnames:6|coltree:3|colmeta:1|heatmap:20" \
       --grid "xy" \
       --break-color 0.25 \
       --cmap bbcry \
       --transform log10 \
       --limits -4 0 \
       --rowsort mean \