rule [
	left [
		edge [ source 2 target 6 label "-" ]
		edge [ source 1 target 7 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
		node [ id 5 label "C" ]
		node [ id 1 label "O" ]
		node [ id 6 label "Cl" ]
		node [ id 7 label "H" ]
		node [ id 8 label "C" ]
		node [ id 9 label "O" ]
		edge [ source 5 target 1 label "-" ]
		edge [ source 9 target 2 label "=" ]
		edge [ source 2 target 8 label "-" ]
	]
	right [
		edge [ source 7 target 6 label "-" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 5
		op "="
		count 2
		edgeLabels [ label ":" ]
	]
	constrainAdj [
		id 8
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
]