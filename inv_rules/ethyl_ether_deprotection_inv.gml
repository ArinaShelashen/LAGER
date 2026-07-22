rule [
	left [
		edge [ source 3 target 4 label "-" ]
		edge [ source 6 target 7 label "-" ]
	]
	context [
		node [ id 2 label "C" ]
		node [ id 3 label "O" ]
		node [ id 4 label "H" ]
		node [ id 5 label "H" ]
		node [ id 6 label "O" ]
		node [ id 7 label "C" ]
		node [ id 8 label "C" ]
		edge [ source 2 target 3 label "-" ]
		edge [ source 5 target 6 label "-" ]
		edge [ source 8 target 7 label "-" ]
	]
	right [
		edge [ source 7 target 3 label "-" ]
		edge [ source 4 target 6 label "-" ]
	]
	constrainAdj [
		id 8
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 7
		op "="
		count 1
		nodeLabels [ label "C" ]
	]
	constrainAdj [
		id 2
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 2
		op "="
		count 0
		edgeLabels [ label ":" ]
	]
]