rule [
	left [
		edge [ source 6 target 7 label "-" ]
		edge [ source 4 target 3 label "-" ]
	]
	context [
		node [ id 1 label "P" ]
		node [ id 2 label "O" ]
		node [ id 3 label "O" ]
		node [ id 4 label "Si" ]
		node [ id 5 label "C" ]
		node [ id 6 label "N" ]
		node [ id 7 label "H" ]
		node [ id 8 label "_X" ]
		node [ id 9 label "C" ]
		edge [ source 8 target 6 label "-" ]
		edge [ source 3 target 1 label "-" ]
		edge [ source 1 target 2 label "=" ]
		edge [ source 1 target 5 label "-" ]
		edge [ source 9 target 6 label "-" ]
	]
	right [
		edge [ source 6 target 4 label "-" ]
		edge [ source 7 target 3 label "-" ]
	]
	constrainAdj [
		id 8
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 4
		op "="
		count 3
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 9
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainLabelAny [ label "_X" labels [ label "C" label "H" ] ]
]