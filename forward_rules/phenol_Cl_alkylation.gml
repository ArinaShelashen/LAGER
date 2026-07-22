rule [
	left [
		edge [ source 1 target 2 label "-" ]
		edge [ source 3 target 4 label "-" ]
	]
	context [
		node [ id 1 label "O" ]
		node [ id 2 label "H" ]
		node [ id 3 label "C" ]
		node [ id 4 label "Cl" ]
		node [ id 5 label "C" ]
		edge [ source 1 target 5 label "-" ]
	]
	right [
		edge [ source 1 target 3 label "-" ]
		edge [ source 2 target 4 label "-" ]
	]
	constrainAdj [
		id 3
		op "="
		count 0
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 3
		op "="
		count 4
		edgeLabels [ label "-" ]
	]
	constrainAdj [
		id 3
		op "<="
		count 2
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 5
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
]