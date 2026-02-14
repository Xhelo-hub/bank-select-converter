@echo off
cd /d "c:\Users\XheladinPalushi\OneDrive - KONSULENCE.AL\Desktop\pdfdemo\Bank_Specific_Converter"
set SECRET_KEY=ec0fbda669d870361ece1a7f5760520e066f692679b65bca77574a39cb279c9a
python -X utf8 -m flask run --port 5002 --host 0.0.0.0
