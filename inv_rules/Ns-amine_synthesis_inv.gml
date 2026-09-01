rule [
	labelType "term"
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 14 target 15 label "-" ]
	]
	context [
		node [ id 1 label "N" ]
		node [ id 14 label "H" ]
		node [ id 15 label "Cl" ]
		node [ id 2 label "S" ]
		node [ id 3 label "O" ]
		node [ id 4 label "O" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "C" ]
		node [ id 8 label "C" ]
		node [ id 9 label "C" ]
		node [ id 10 label "C" ]
		node [ id 11 label "N+" ]
		node [ id 12 label "O" ]
		node [ id 13 label "O-" ]
		node [ id 16 label "_X" ]
		node [ id 17 label "C" ]
		edge [ source 2 target 3 label "=" ]
		edge [ source 2 target 4 label "=" ]
		edge [ source 2 target 5 label "-" ]
		edge [ source 5 target 6 label ":" ]
		edge [ source 6 target 7 label ":" ]
		edge [ source 7 target 8 label ":" ]
		edge [ source 8 target 9 label ":" ]
		edge [ source 9 target 10 label ":" ]
		edge [ source 10 target 5 label ":" ]
		edge [ source 8 target 11 label "-" ]
		edge [ source 11 target 12 label "=" ]
		edge [ source 11 target 13 label "-" ]
		edge [ source 1 target 16 label "-" ]
		edge [ source 1 target 17 label "-" ]
	]
	right [
		edge [ source 1 target 14 label "-" ]
		edge [ source 2 target 15 label "-" ]
	]
	constrainAdj [
		id 16
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 17
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainLabelAny [ label "_X" labels [ label "C" label "H" ] ]
]