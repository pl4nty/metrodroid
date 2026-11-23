# -*- mode: makefile; indent-tabs-mode: tabs; tab-width: 2 -*-
MDROOT = ../..

include ../Makefile.github

GITHUB_PROJECT := Kdroidwin/suicanfc-kd
GITHUB_COMMIT  := f8cc01d79db6dfdf75e5ea125a3a2c3cc6486823
ASSETS          = app/src/main/assets
DATA_FILES      = $(ASSETS)/StationCode.csv $(ASSETS)/StationCodeExtra.csv $(ASSETS)/BusCode.csv $(ASSETS)/BusCodeExtra.csv LICENSE
MERGED          = rail_stations.csv rail_operators.csv rail_lines.csv bus_stations.csv bus_operators.csv bus_lines.csv
CSV2PB          = python3 $(MDST)/csv2pb.py -V "$(call github-get-ts,commit_info.json)" -l ja -L ja -n NOTICE

all: suica_rail.mdst suica_rail.csv suica_bus.mdst suica_bus.csv

commit_info.json:
	$(call github-get-metadata,$(GITHUB_PROJECT),$(GITHUB_COMMIT))

$(DATA_FILES): commit_info.json
	$(call github-fetch-file-md,$(GITHUB_PROJECT),$@)

NOTICE: NOTICE-prefix LICENSE
	cat $^ > $@

sha512ok: sha512sums $(DATA_FILES)
	$(call sha512)

$(MERGED) &: mdst sha512ok legacy_rail.csv legacy_bus.csv
	python3 $(MDST)/suica2csv.py -l . -s $(ASSETS) -o .

suica_rail.mdst: mdst commit_info.json rail_stations.csv rail_operators.csv rail_lines.csv NOTICE
	$(CSV2PB) -p rail_operators.csv -r rail_lines.csv -o $@ rail_stations.csv

suica_bus.mdst: mdst commit_info.json bus_stations.csv bus_operators.csv bus_lines.csv NOTICE
	$(CSV2PB) -p bus_operators.csv -r bus_lines.csv -o $@ bus_stations.csv

copy: suica_rail.copy suica_bus.copy

clean:
	rm -f suica_rail.mdst suica_rail.csv suica_bus.mdst suica_bus.csv commit_info.json NOTICE sha512ok $(MERGED) $(DATA_FILES)
	rm -rf app

include ../Makefile.common
