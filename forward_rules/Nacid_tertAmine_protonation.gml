rule [
	left [
		node [ id 1 label "N" ]
		node [ id 3 label "O" ]
		edge [ source 2 target 3 label "-" ]
	]
	context [
		node [ id 2 label "H" ]
		node [ id 4 label "N" ]
		node [ id 5 label "C" ]
		node [ id 6 label "C" ]
		node [ id 7 label "C" ]
		edge [ source 3 target 4 label "-" ]
		edge [ source 7 target 1 label "-" ]
		edge [ source 6 target 1 label "-" ]
		edge [ source 1 target 5 label "-" ]
	]
	right [
		node [ id 1 label "N+" ]
		node [ id 3 label "O-" ]
		edge [ source 1 target 2 label "-" ]
	]
	constrainAdj [
		id 5
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 4
		op ">="
		count 2
		nodeLabels [ label "O" ]
	]
	constrainAdj [
		id 7
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
	constrainAdj [
		id 6
		op "="
		count 0
		nodeLabels [ label "O" ]
		edgeLabels [ label "=" ]
	]
]